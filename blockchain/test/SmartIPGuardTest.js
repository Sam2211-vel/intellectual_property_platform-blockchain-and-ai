const IPP = artifacts.require("IPP");

contract("IPP", accounts => {

  it("should store and retrieve asset details", async () => {
    const instance = await SmartIPGuard.deployed();

    const fileHash = "hash123";
    const cid = "cid123";
    const owner = "UserA";

    await instance.storeAsset(fileHash, cid, owner);

    const asset = await instance.getAsset(fileHash);

    assert.equal(asset[0], fileHash, "File hash mismatch");
    assert.equal(asset[1], cid, "CID mismatch");
    assert.equal(asset[2], owner, "Owner mismatch");
  });

});
