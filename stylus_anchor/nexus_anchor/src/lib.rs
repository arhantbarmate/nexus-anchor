#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use alloc::vec::Vec;
use stylus_sdk::{
    alloy_primitives::{keccak256, FixedBytes, Uint},
    prelude::*,
    storage::{StorageBool, StorageMap, StorageU64},
};

type U64 = Uint<64, 1>;

#[storage]
#[entrypoint]
pub struct NexusAnchor {
    authorized_nodes: StorageMap<FixedBytes<32>, StorageBool>,
    counters: StorageMap<FixedBytes<32>, StorageU64>,
    approved_firmware: StorageMap<FixedBytes<32>, StorageBool>,
}

#[public]
impl NexusAnchor {
    pub fn verify_receipt(
        &mut self,
        hw_id: FixedBytes<32>,
        fw_hash: FixedBytes<32>,
        exec_hash: FixedBytes<32>,
        counter: u64,
        claimed_digest: FixedBytes<32>,
    ) -> Result<(), Vec<u8>> {
        let counter_uint: U64 = U64::from(counter);

        if !self.authorized_nodes.get(hw_id) {
            return Err(b"Unauthorized Hardware".to_vec());
        }

        if !self.approved_firmware.get(fw_hash) {
            return Err(b"Firmware Not Approved".to_vec());
        }

        let last_counter: U64 = self.counters.get(hw_id);
        if counter_uint <= last_counter {
            return Err(b"Replay Detected".to_vec());
        }

        let counter_bytes = counter.to_be_bytes();

        let mut material = Vec::with_capacity(116);
        material.extend_from_slice(b"NEXUS_RCT_V1");
        material.extend_from_slice(hw_id.as_slice());
        material.extend_from_slice(fw_hash.as_slice());
        material.extend_from_slice(exec_hash.as_slice());
        material.extend_from_slice(&counter_bytes);

        let reconstructed = keccak256(&material);

        if reconstructed != claimed_digest {
            return Err(b"Digest Mismatch".to_vec());
        }

        self.counters.insert(hw_id, counter_uint);

        Ok(())
    }

    pub fn authorize_node(&mut self, node_id: FixedBytes<32>) {
        self.authorized_nodes.insert(node_id, true);
    }

    pub fn revoke_node(&mut self, node_id: FixedBytes<32>) {
        self.authorized_nodes.insert(node_id, false);
    }

    pub fn approve_firmware(&mut self, fw_hash: FixedBytes<32>) {
        self.approved_firmware.insert(fw_hash, true);
    }

    pub fn revoke_firmware(&mut self, fw_hash: FixedBytes<32>) {
        self.approved_firmware.insert(fw_hash, false);
    }

    pub fn is_node_authorized(&self, node_id: FixedBytes<32>) -> bool {
        self.authorized_nodes.get(node_id)
    }

    pub fn is_firmware_approved(&self, fw_hash: FixedBytes<32>) -> bool {
        self.approved_firmware.get(fw_hash)
    }

    pub fn get_counter(&self, node_id: FixedBytes<32>) -> u64 {
        let counter_uint: U64 = self.counters.get(node_id);
        counter_uint.try_into().unwrap_or(u64::MAX)
    }
}
