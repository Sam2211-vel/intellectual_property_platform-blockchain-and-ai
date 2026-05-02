// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract IPP {

    struct Asset {
        string fileHash;
        string cid;
        string owner;
        uint256 timestamp;
    }

    // fileHash => Asset
    mapping(string => Asset) private assets;

    // Event for logging
    event AssetStored(
        string fileHash,
        string cid,
        string owner,
        uint256 timestamp
    );

    /**
     * Store IP asset proof
     */
    function storeAsset(
        string memory _fileHash,
        string memory _cid,
        string memory _owner
    ) public {
        require(bytes(assets[_fileHash].fileHash).length == 0,
            "Asset already exists");

        assets[_fileHash] = Asset({
            fileHash: _fileHash,
            cid: _cid,
            owner: _owner,
            timestamp: block.timestamp
        });

        emit AssetStored(_fileHash, _cid, _owner, block.timestamp);
    }

    /**
     * Retrieve asset details
     */
    function getAsset(string memory _fileHash)
        public
        view
        returns (
            string memory,
            string memory,
            string memory,
            uint256
        )
    {
        Asset memory asset = assets[_fileHash];
        return (
            asset.fileHash,
            asset.cid,
            asset.owner,
            asset.timestamp
        );
    }
}
