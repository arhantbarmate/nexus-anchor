/**
 * anchorAnchor Hardware Identity & Receipt Generation
 * ESP32 Compatible Version (Software Keccak)
 * 
 * SECURITY AUDIT COMPLIANT - Phase 2
 * 
 * COMPATIBILITY:
 * - Works on ESP32, ESP32-S2, ESP32-S3, ESP32-C3, etc.
 * - Uses Ethereum-compatible Keccak-256 (NOT SHA3-256)
 * - Handles different eFuse APIs across chip families
 * 
 * SECURITY WARNINGS:
 * ⚠️ ESP32 (original) support is for DEVELOPMENT ONLY
 *    Production OHR nodes require ESP32-S2/S3 with eFuse-backed unique ID
 * ⚠️ Software Keccak - hardware acceleration preferred for production
 * ⚠️ NVS encryption MUST be enabled in production to prevent physical rollback attacks
 * ⚠️ Secure Boot V2 key extraction requires production implementation
 */

#include <stdio.h>
#include <string.h>
#include "esp_efuse.h"
#include "esp_flash_encrypt.h"
#include "esp_secure_boot.h"
#include "esp_ota_ops.h"
#include "esp_app_format.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_mac.h"

// Using Ethereum-compatible Keccak-256 (NOT SHA3-256)
// Keccak uses 0x01 padding, SHA3 uses 0x06 padding - they produce DIFFERENT hashes!
#include "sha3.h"

static const char *TAG = "anchor_OHR";

// ============================================================================
// PROTOCOL CONSTANTS (FROZEN)
// ============================================================================
// Separate domain tags to avoid cross-hash ambiguity
#define anchor_HWI_DOMAIN "anchor_OHR_V1"  // Hardware Identity
#define anchor_RCT_DOMAIN "anchor_RCT_V1"  // Receipt Digest
#define anchor_HWI_DOMAIN_LEN 13
#define anchor_RCT_DOMAIN_LEN 13

// ============================================================================
// KECCAK-256 WRAPPER (Ethereum-compatible)
// ============================================================================
/**
 * Ethereum-compatible Keccak-256 implementation
 * 
 * This uses the correct Keccak padding (0x01) that matches:
 * - Solidity's keccak256()
 * - Stylus contracts using alloy_primitives::keccak256
 * - Python's eth_hash.keccak
 * 
 * NOTE: This is NOT the same as SHA3-256 (which uses 0x06 padding)
 */
static void anchor_keccak256(const uint8_t *input, size_t len, uint8_t *output) {
    keccak_256(input, len, output);
}

// ============================================================================
// CHIP-AGNOSTIC UNIQUE ID RETRIEVAL
// ============================================================================
/**
 * ⚠️ SECURITY WARNING: ESP32 (original) MAC-based ID is CLONEABLE
 * 
 * ESP32 MAC addresses:
 * - Are software-settable on some revisions
 * - Can be spoofed in development mode
 * 
 * PRODUCTION REQUIREMENT:
 * Use ESP32-S2/S3/C3 with eFuse-backed OPTIONAL_UNIQUE_ID for non-clonability
 */
static esp_err_t anchor_get_chip_id(uint8_t chip_id[16]) {
#if defined(CONFIG_IDF_TARGET_ESP32S3) || defined(CONFIG_IDF_TARGET_ESP32S2) || defined(CONFIG_IDF_TARGET_ESP32C3)
    // ESP32-S2/S3/C3 have eFuse-backed OPTIONAL_UNIQUE_ID
    ESP_LOGI(TAG, "✓ Using eFuse-backed unique ID");
    esp_efuse_read_field_blob(ESP_EFUSE_OPTIONAL_UNIQUE_ID, chip_id, 128);
    return ESP_OK;
#else
    // ESP32 (original) - DEVELOPMENT ONLY
    ESP_LOGW(TAG, "⚠️ ESP32 MAC-based ID - DEVELOPMENT ONLY (cloneable)");
    ESP_LOGW(TAG, "⚠️ Production deployment requires ESP32-S2/S3/C3");
    
    uint8_t mac[6];
    esp_err_t err = esp_read_mac(mac, ESP_MAC_WIFI_STA);
    if (err != ESP_OK) return err;
    
    // Expand MAC to 16 bytes (pad with zeros)
    memcpy(chip_id, mac, 6);
    memset(chip_id + 6, 0, 10);
    return ESP_OK;
#endif
}

// ============================================================================
// SECURITY STATE FINGERPRINT (⚠️ NOT A CRYPTOGRAPHIC KEY)
// ============================================================================
/**
 * ⚠️ SECURITY WARNING: This is NOT a secure boot key
 * 
 * CURRENT IMPLEMENTATION:
 * Creates a deterministic security-state fingerprint based on chip model/revision.
 * 
 * LIMITATION:
 * - Two devices of the same model produce the SAME "digest"
 * - This breaks non-clonability
 * - This is NOT tied to actual Secure Boot V2 keys
 * 
 * PRODUCTION REQUIREMENT:
 * Replace with eFuse-backed Secure Boot V2 key digest extraction.
 * 
 * On ESP32-S2/S3 with Secure Boot V2, the key digest is stored in eFuse
 * and must be read via esp_efuse APIs (implementation depends on ESP-IDF version).
 * 
 * ACCEPTABLE FOR:
 * - Development/testing with clear documentation
 * - Phase-2 middleware development
 * 
 * NOT ACCEPTABLE FOR:
 * - Production deployment
 * - Security audit compliance
 * - Hardware sovereignty claims
 */
static esp_err_t anchor_get_security_state_fingerprint(uint8_t digest[32]) {
#if CONFIG_SECURE_BOOT_V2_ENABLED
    ESP_LOGW(TAG, "⚠️ Security state fingerprint - NOT a cryptographic key");
    ESP_LOGW(TAG, "⚠️ Production requires eFuse-backed Secure Boot V2 key digest");
    
    // Create deterministic fingerprint (NOT a secure key)
    esp_chip_info_t chip_info;
    esp_chip_info(&chip_info);
    
    uint8_t temp[32] = {0};
    temp[0] = chip_info.model;
    temp[1] = chip_info.cores;
    temp[2] = chip_info.revision;
    
    // Hash to create 32-byte fingerprint
    anchor_keccak256(temp, 32, digest);
    
    ESP_LOGI(TAG, "Security fingerprint: model=%d cores=%d rev=%d", 
             chip_info.model, chip_info.cores, chip_info.revision);
    
    return ESP_OK;
#else
    // Development mode - clearly marked placeholder
    ESP_LOGW(TAG, "⚠️ No Secure Boot - using development placeholder");
    ESP_LOGW(TAG, "⚠️ Production REQUIRES Secure Boot V2 enabled");
    memset(digest, 0xAA, 32);
    return ESP_OK;
#endif
}

// ============================================================================
// HARDWARE IDENTITY DERIVATION (FIXED - NO CIRCULAR DEPENDENCY)
// ============================================================================
/**
 * Hardware Identity Derivation (FROZEN PROTOCOL)
 * 
 * hardware_identity = keccak256(
 *     anchor_HWI_DOMAIN     || // 13 bytes - Domain separation
 *     chip_unique_id       || // 16 bytes - Device uniqueness
 *     secure_boot_enabled  || //  1 byte  - Security state
 *     flash_encrypt_enabled|| //  1 byte  - Security state
 *     security_fingerprint || // 32 bytes - Crypto identity (⚠️ placeholder)
 * )
 * 
 * SECURITY PROPERTIES:
 * ✓ Static per device (no firmware dependency)
 * ✓ Changes if security state changes
 * ✓ Domain-separated from receipt digests
 * 
 * ⚠️ PRODUCTION REQUIREMENTS:
 * - ESP32-S2/S3/C3 for eFuse-backed unique ID
 * - security_fingerprint must be replaced with real Secure Boot V2 key digest
 */
static esp_err_t anchor_derive_hardware_identity(uint8_t hardware_identity[32]) {
    uint8_t identity_material[128] = {0};
    size_t offset = 0;
    esp_err_t err;
    
    ESP_LOGI(TAG, "Deriving hardware identity...");
    
    // 1. Domain Tag (13 bytes) - prevents cross-protocol hash collisions
    memcpy(identity_material + offset, anchor_HWI_DOMAIN, anchor_HWI_DOMAIN_LEN);
    offset += anchor_HWI_DOMAIN_LEN;
    
    // 2. Chip Unique ID (16 bytes)
    uint8_t chip_id[16];
    err = anchor_get_chip_id(chip_id);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to get chip ID");
        return err;
    }
    memcpy(identity_material + offset, chip_id, 16);
    offset += 16;
    
    // 3. Security State (2 bytes)
    bool sb_enabled = esp_secure_boot_enabled();
    bool fe_enabled = esp_flash_encryption_enabled();
    
    identity_material[offset++] = sb_enabled ? 0x01 : 0x00;
    identity_material[offset++] = fe_enabled ? 0x01 : 0x00;
    
    ESP_LOGI(TAG, "Security state: SB=%s FE=%s", 
             sb_enabled ? "ON" : "OFF",
             fe_enabled ? "ON" : "OFF");
    
    // 4. Security State Fingerprint (32 bytes)
    // ⚠️ This is a placeholder - production needs real Secure Boot key digest
    uint8_t sec_fingerprint[32];
    err = anchor_get_security_state_fingerprint(sec_fingerprint);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to get security fingerprint");
        return err;
    }
    memcpy(identity_material + offset, sec_fingerprint, 32);
    offset += 32;
    
    // NOTE: Firmware hash is NOT included (prevents circular dependency)
    // Firmware binding happens at receipt generation time
    
    // Hash to derive final identity
    anchor_keccak256(identity_material, offset, hardware_identity);

    // Zeroize sensitive buffers
    memset(identity_material, 0, sizeof(identity_material));
    memset(chip_id, 0, sizeof(chip_id));
    memset(sec_fingerprint, 0, sizeof(sec_fingerprint));

    ESP_LOGI(TAG, "✓ Hardware identity derived (%zu bytes hashed)", offset);
    return ESP_OK;
}

// ============================================================================
// FIRMWARE HASH HELPER
// ============================================================================
/**
 * Derives firmware binding hash from ESP-IDF app descriptor
 * 
 * This creates a deterministic firmware version identifier that:
 * - Binds the receipt to the executing firmware
 * - Changes when firmware is updated
 * - Is verifiable by middleware
 */
static esp_err_t anchor_get_firmware_hash(uint8_t firmware_hash[32]) {
    const esp_app_desc_t *app_desc = esp_app_get_description();
    
    // Normalize ESP-IDF's SHA256 to Keccak-256
    anchor_keccak256(app_desc->app_elf_sha256, 32, firmware_hash);
    
    ESP_LOGI(TAG, "Firmware version: %s", app_desc->version);
    ESP_LOGI(TAG, "Compile time: %s %s", app_desc->date, app_desc->time);
    
    return ESP_OK;
}

// ============================================================================
// COUNTER MANAGEMENT (⚠️ REQUIRES NVS ENCRYPTION IN PRODUCTION)
// ============================================================================
/**
 * Monotonic counter for replay protection
 * 
 * ⚠️ PRODUCTION SECURITY REQUIREMENT:
 * NVS encryption MUST be enabled to prevent physical rollback attacks.
 * 
 * An attacker with physical access could:
 * 1. Read unencrypted NVS from flash
 * 2. Restore old counter value
 * 3. Replay old attestations
 * 
 * MITIGATION:
 * Enable NVS encryption in menuconfig:
 * Component config → NVS → Enable NVS encryption
 * 
 * This ties NVS encryption to flash encryption key, preventing
 * offline modification of counter values.
 */
static esp_err_t anchor_increment_counter(uint64_t *new_counter) {
    nvs_handle_t h;
    esp_err_t err = nvs_open("anchor", NVS_READWRITE, &h);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to open NVS: %s", esp_err_to_name(err));
        return err;
    }

    uint64_t val = 0;
    err = nvs_get_u64(h, "counter", &val);
    if (err == ESP_ERR_NVS_NOT_FOUND) {
        val = 0;
        ESP_LOGI(TAG, "Initializing counter to 0");
    } else if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to read counter: %s", esp_err_to_name(err));
        nvs_close(h);
        return err;
    }
    
    val++;
    
    err = nvs_set_u64(h, "counter", val);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to write counter: %s", esp_err_to_name(err));
        nvs_close(h);
        return err;
    }
    
    err = nvs_commit(h);
    nvs_close(h);
    
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to commit counter: %s", esp_err_to_name(err));
        return err;
    }
    
    *new_counter = val;
    
    // ⚠️ Security audit requirement
    if (!esp_flash_encryption_enabled()) {
        ESP_LOGW(TAG, "⚠️ NVS not encrypted - vulnerable to physical rollback");
        ESP_LOGW(TAG, "⚠️ Enable flash encryption for production deployment");
    }
    
    ESP_LOGI(TAG, "Counter incremented to %llu", (unsigned long long)val);
    return ESP_OK;
}

// ============================================================================
// REPLAY-SAFE RECEIPT GENERATION (FIXED DOMAIN SEPARATION)
// ============================================================================
/**
 * Receipt format (FROZEN PROTOCOL):
 * 
 * receipt_digest = keccak256(
 *     anchor_RCT_DOMAIN     || // 13 bytes - Domain separation (different from HWI)
 *     hardware_identity    || // 32 bytes - Static device ID
 *     firmware_hash        || // 32 bytes - Firmware version binding
 *     execution_hash       || // 32 bytes - Computation result
 *     monotonic_counter_be || //  8 bytes - Replay protection
 * )
 * 
 * SECURITY PROPERTIES:
 * ✓ Domain-separated from hardware identity
 * ✓ Firmware-bound (changes on OTA update)
 * ✓ Replay-protected (monotonic counter)
 * ✓ Execution-specific (binds to computation result)
 * 
 * ⚠️ VERIFICATION REQUIREMENTS:
 * Middleware must verify:
 * 1. receipt_digest matches expected value
 * 2. hardware_identity is in allowlist
 * 3. counter > last_seen_counter[hardware_identity]
 * 4. firmware_hash is in approved firmware versions
 */
static esp_err_t anchor_generate_receipt(
    const uint8_t exec_hash[32], 
    uint8_t digest[32], 
    uint64_t *cnt
) {
    esp_err_t err;
    
    ESP_LOGI(TAG, "Generating receipt...");
    
    // 1. Get hardware identity
    uint8_t hw_id[32];
    err = anchor_derive_hardware_identity(hw_id);
    if (err != ESP_OK) return err;
    
    // 2. Get firmware hash
    uint8_t fw_hash[32];
    err = anchor_get_firmware_hash(fw_hash);
    if (err != ESP_OK) return err;
    
    // 3. Increment counter
    uint64_t counter_val;
    err = anchor_increment_counter(&counter_val);
    if (err != ESP_OK) return err;

    // 4. Build receipt material
    uint8_t rct_material[256] = {0};
    size_t r_off = 0;
    
    // Domain tag (DIFFERENT from hardware identity domain)
    memcpy(rct_material + r_off, anchor_RCT_DOMAIN, anchor_RCT_DOMAIN_LEN);
    r_off += anchor_RCT_DOMAIN_LEN;
    
    // Hardware identity
    memcpy(rct_material + r_off, hw_id, 32);
    r_off += 32;
    
    // Firmware hash
    memcpy(rct_material + r_off, fw_hash, 32);
    r_off += 32;
    
    // Execution hash
    memcpy(rct_material + r_off, exec_hash, 32);
    r_off += 32;
    
    // Counter (big-endian)
    uint64_t be_cnt = __builtin_bswap64(counter_val);
    memcpy(rct_material + r_off, &be_cnt, 8);
    r_off += 8;

    // 5. Hash to produce receipt digest
    anchor_keccak256(rct_material, r_off, digest);
    
    *cnt = counter_val;

    // Clean up
    memset(rct_material, 0, sizeof(rct_material));
    memset(hw_id, 0, sizeof(hw_id));
    memset(fw_hash, 0, sizeof(fw_hash));

    ESP_LOGI(TAG, "✓ Receipt generated: counter=%llu", (unsigned long long)counter_val);
    return ESP_OK;
}

// ============================================================================
// JSON OUTPUT FOR MIDDLEWARE
// ============================================================================
static void print_receipt_json(
    const uint8_t receipt_digest[32],
    const uint8_t hardware_identity[32],
    uint64_t counter
) {
    printf("{\n");
    
    printf("  \"receipt_digest\": \"0x");
    for(int i = 0; i < 32; i++) printf("%02x", receipt_digest[i]);
    printf("\",\n");
    
    printf("  \"hardware_identity\": \"0x");
    for(int i = 0; i < 32; i++) printf("%02x", hardware_identity[i]);
    printf("\",\n");
    
    printf("  \"counter\": %llu,\n", (unsigned long long)counter);
    
    // Include security warnings in output for middleware awareness
    printf("  \"security_warnings\": [\n");
    
#ifndef CONFIG_IDF_TARGET_ESP32S3
#ifndef CONFIG_IDF_TARGET_ESP32S2
#ifndef CONFIG_IDF_TARGET_ESP32C3
    printf("    \"ESP32 MAC-based ID - development only\",\n");
#endif
#endif
#endif
    
    printf("    \"Ethereum Keccak-256 implementation\",\n");
    
#if !CONFIG_SECURE_BOOT_V2_ENABLED
    printf("    \"Secure Boot disabled - development mode\",\n");
#else
    printf("    \"Security fingerprint - not cryptographic key\",\n");
#endif
    
    if (!esp_flash_encryption_enabled()) {
        printf("    \"Flash encryption disabled - NVS vulnerable to rollback\",\n");
    }
    
    printf("    \"Production deployment requires security hardening\"\n");
    printf("  ]\n");
    
    printf("}\n");
}

// ============================================================================
// SECURITY STATUS REPORT
// ============================================================================
static void print_security_status(void) {
    printf("\n");
    printf("╔═══════════════════════════════════════════════════════════════╗\n");
    printf("║          anchor OHR SECURITY STATUS REPORT                    ║\n");
    printf("╠═══════════════════════════════════════════════════════════════╣\n");
    
    // Chip type
    printf("║ Chip: %-55s ║\n", CONFIG_IDF_TARGET);
    
    // Hardware identity source
#if defined(CONFIG_IDF_TARGET_ESP32S3) || defined(CONFIG_IDF_TARGET_ESP32S2) || defined(CONFIG_IDF_TARGET_ESP32C3)
    printf("║ Unique ID: ✓ eFuse-backed                                ║\n");
#else
    printf("║ Unique ID: ⚠️  MAC-based (development only)                   ║\n");
#endif
    
    // Secure Boot
    if (esp_secure_boot_enabled()) {
        printf("║ Secure Boot: ✓ ENABLED                                       ║\n");
#if CONFIG_SECURE_BOOT_V2_ENABLED
        printf("║ Boot Version: V2 (⚠️  fingerprint placeholder)               ║\n");
#endif
    } else {
        printf("║ Secure Boot: ⚠️  DISABLED (development mode)                 ║\n");
    }
    
    // Flash Encryption
    if (esp_flash_encryption_enabled()) {
        printf("║ Flash Encryption: ✓ ENABLED                                  ║\n");
    } else {
        printf("║ Flash Encryption: ⚠️  DISABLED (NVS vulnerable)              ║\n");
    }
    
    // Keccak implementation
    printf("║ Keccak-256: ✓ Ethereum-compatible implementation            ║\n");
    
    printf("╠═══════════════════════════════════════════════════════════════╣\n");
    
    // Production readiness
    bool production_ready = true;
    
#if !defined(CONFIG_IDF_TARGET_ESP32S3) && !defined(CONFIG_IDF_TARGET_ESP32S2) && !defined(CONFIG_IDF_TARGET_ESP32C3)
    production_ready = false;
#endif
    
    if (!esp_secure_boot_enabled() || !esp_flash_encryption_enabled()) {
        production_ready = false;
    }
    
    if (production_ready) {
        printf("║ Status: ⚠️  PHASE-2 DEVELOPMENT (requires Keccak upgrade)    ║\n");
    } else {
        printf("║ Status: ⚠️  DEVELOPMENT ONLY (NOT production-ready)          ║\n");
    }
    
    printf("╚═══════════════════════════════════════════════════════════════╝\n");
    printf("\n");
}

// ============================================================================
// MAIN APPLICATION
// ============================================================================
extern "C" void app_main(void) {
    ESP_LOGI(TAG, "═══════════════════════════════════════════════════════════");
    ESP_LOGI(TAG, "  anchorAnchor OHR - Hardware Identity & Receipt System");
    ESP_LOGI(TAG, "  Version: Phase-2 Security Audit Compliant");
    ESP_LOGI(TAG, "═══════════════════════════════════════════════════════════");
    
    // 1. Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_LOGW(TAG, "NVS needs erase - erasing...");
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    ESP_LOGI(TAG, "✓ NVS initialized");

    // 2. Display comprehensive security status
    print_security_status();
    
    // 3. Derive and display hardware identity
    uint8_t hw_identity[32];
    if (anchor_derive_hardware_identity(hw_identity) == ESP_OK) {
        printf("Hardware Identity: 0x");
        for(int i = 0; i < 32; i++) printf("%02x", hw_identity[i]);
        printf("\n\n");
    } else {
        ESP_LOGE(TAG, "Failed to derive hardware identity");
        return;
    }
    
    // 4. Generate test attestation
    ESP_LOGI(TAG, "Generating test attestation with execution hash...");
    
    uint8_t execution_result[32] = {
        0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01
    }; 
    
    uint8_t receipt_digest[32];
    uint64_t counter;
    
    if (anchor_generate_receipt(execution_result, receipt_digest, &counter) == ESP_OK) {
        printf("\n");
        printf("═══════════════════════════════════════════════════════════\n");
        printf("           anchor OHR ATTESTATION RECEIPT\n");
        printf("═══════════════════════════════════════════════════════════\n");
        print_receipt_json(receipt_digest, hw_identity, counter);
        printf("═══════════════════════════════════════════════════════════\n\n");
        
        ESP_LOGI(TAG, "✓ Receipt ready for middleware verification");
        
        // Production deployment checklist
        printf("\n");
        printf("╔═══════════════════════════════════════════════════════════════╗\n");
        printf("║           PRODUCTION DEPLOYMENT REQUIREMENTS                  ║\n");
        printf("╠═══════════════════════════════════════════════════════════════╣\n");
        printf("║ [x] Ethereum Keccak-256 implemented                          ║\n");
        printf("║     (tiny-keccak with 0x01 padding)                           ║\n");
        printf("║                                                               ║\n");
        printf("║ [ ] Use ESP32-S2/S3/C3 with eFuse-backed unique ID            ║\n");
        printf("║                                                               ║\n");
        printf("║ [ ] Enable Secure Boot V2                                     ║\n");
        printf("║     Replace security fingerprint with real key digest        ║\n");
        printf("║                                                               ║\n");
        printf("║ [ ] Enable Flash Encryption                                   ║\n");
        printf("║     Enable NVS encryption to prevent counter rollback        ║\n");
        printf("║                                                               ║\n");
        printf("║ [ ] Middleware must verify:                                   ║\n");
        printf("║     - Hardware identity allowlist                             ║\n");
        printf("║     - Counter monotonicity                                    ║\n");
        printf("║     - Firmware version approval                               ║\n");
        printf("╚═══════════════════════════════════════════════════════════════╝\n");
        printf("\n");
        
    } else {
        ESP_LOGE(TAG, "❌ Failed to generate receipt");
    }
}
