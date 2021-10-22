import time
from hashlib import sha256
import json
from time import perf_counter

class Block():
    @property
    def _hash(self):
        return str(sha256((self.data + self.nonce + self.previousHash + self.timestamp).encode('utf-8')).hexdigest())
    def __init__(self, data: str, previousHash: str):
        self.previousHash : str = previousHash
        self.data :str = data
        self.timestamp : str= str(time.asctime())
        self.nonce: str = ""
        self.hash = self._hash

    def mineBlock(self, difficulty : int = 4):
        init = 0
        start_seq = difficulty*"0"
        while not str(sha256((self.data + str(init) + self.previousHash + self.timestamp).encode('utf-8')).hexdigest()).startswith(start_seq):
            init += 1
        self.nonce = str(init)
        self.hash = self._hash
        return self
    def changeBlock(self):
        self.data = "Vsichni mi dluzite prasule."
        return self

if __name__ == "__main__":
    difficulty = 4
    change = False
    print(f"Obtížnost nastavena na {difficulty}.")
    blockchain = []
    print("Těžím první block...")
    ref = perf_counter()
    blockchain.append(Block("Ahoj, ja jsem prvni blok", "0").mineBlock(difficulty))
    print(f"Blok 1 vytěžen za {perf_counter() - ref : .2f} sekund.")
    print("Těžím druhý block...")
    ref = perf_counter()
    if change:
        blockchain.append(Block("Ja jsem druhy.", blockchain[-1].hash).mineBlock(difficulty).changeBlock())
    else:
        blockchain.append(Block("Ja jsem druhy.", blockchain[-1].hash).mineBlock(difficulty))
    print(f"Blok 2 vytěžen za {perf_counter() - ref : .2f} sekund.")
    print("Těžím třetí block...")
    ref = perf_counter()
    blockchain.append(Block("Ahoj, ja jsem prvni blok", blockchain[-1].hash).mineBlock(difficulty))
    print(f"Blok 3 vytěžen za {perf_counter() - ref : .2f} sekund.")

    print(json.dumps([block.__dict__ for block in blockchain], indent=4, sort_keys=True))
    with open("jout.json", "w") as jout:
        json.dump([block.__dict__ for block in blockchain], jout, indent=4, sort_keys=True)

    def isChainValid() -> bool:
        for block in blockchain:
            if str(sha256((block.data + block.nonce + block.previousHash + block.timestamp).encode('utf-8')).hexdigest()) != block.hash:
                return False
        return True

    print("Kontrola Blockchainu: " + str(isChainValid()))
