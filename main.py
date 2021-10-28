import time
from hashlib import sha256
import json
from time import perf_counter


class Wallet:
    def __init__(self, name: str):
        self.name: str = name
        self.UTXOs: list = []

    def sendFunds(self, recipent, value: float):
        """Iniciuje transakci, vrací objekt třídy Transaction, který lze poslat na BlockChain"""
        bill = value
        neededUTXOs = []
        for tInput in self.UTXOs:
            if bill > 0:
                bill -= tInput.UTXO
                neededUTXOs.append(tInput)
        transaction = Transaction(self.name, recipent.name, value, neededUTXOs)
        for UTXO in neededUTXOs:
            self.UTXOs.remove(UTXO)
        self.UTXOs.append(TransactionInput(transaction.outputs[0]))
        return transaction

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class TransactionOutput:
    def __init__(self, recipent: str, value: float, parentTransactionId: str):
        self.receipent: str = recipent
        self.value: float = value
        self.parentTransactionId: str = parentTransactionId
        self.id = str(
            sha256(
                (self.receipent + str(self.value) + self.parentTransactionId).encode(
                    "utf-8"
                )
            ).hexdigest()
        )


class TransactionInput:  # upraveno oproti zadání
    def __init__(self, tOut: TransactionOutput):
        self.transactionOutputId: str = tOut.id
        self.UTXO: float = tOut.value

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class Transaction:
    def __init__(self, sender: str, reciepent: str, value: float, inputs: list):
        self.sender: str = sender
        self.reciepent: str = reciepent
        self.value: float = value
        self.inputs: list = inputs
        self.id: str = self.calculateHash()
        self.outputs: [TransactionOutput, TransactionOutput] = self.calculateOutputs()

    def calculateHash(self) -> str:
        return str(
            sha256(
                (self.sender + self.reciepent + str(self.value)).encode("utf-8")
            ).hexdigest()
        )

    def calculateOutputs(self) -> [TransactionOutput, TransactionOutput]:
        """Vypočte výstupy transakce; přeplatek odesílatele a obdrženou částku příjemce"""
        balance = 0
        for tInput in self.inputs:
            balance += tInput.UTXO
        if balance < self.value:
            raise ValueError("Not enough money provided for a transaction!")
        bill = self.value
        lastValue = 0
        copyInputs = list(self.inputs)  # shallow copy
        self.inputs = []
        for tInput in copyInputs:
            bill -= tInput.UTXO
            self.inputs.append(tInput)
            if bill < 0:
                lastValue = abs(bill)
                break
        return TransactionOutput(self.sender, lastValue, self.id), TransactionOutput(
            self.reciepent, self.value, self.id
        )

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class Block:
    @property
    def _hash(self):
        return str(
            sha256(
                (
                    str(self.data) + self.nonce + self.previousHash + self.timestamp
                ).encode("utf-8")
            ).hexdigest()
        )

    def __init__(
        self,
        data: [
            Transaction,
        ],
        previousHash: str,
    ):
        self.previousHash: str = previousHash
        self.data = data
        self.timestamp: str = str(time.asctime())
        self.nonce: str = ""
        self.hash = self._hash

    def mineBlock(self):
        init = 0
        start_seq = difficulty * "0"
        while not str(
            sha256(
                (
                    str(self.data) + str(init) + self.previousHash + self.timestamp
                ).encode("utf-8")
            ).hexdigest()
        ).startswith(start_seq):
            init += 1
        self.nonce = str(init)
        self.hash = self._hash
        return self

    @classmethod
    def configDifficulty(cls, diff: int):
        cls.difficulty = diff

    # def changeBlock(self):
    #    self.data = "Vsichni mi dluzite prasule."
    #    return self

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class BlockChain:
    def __init__(self):
        self.chain = []
        self.wallets = []
        self.unminedTransactions = []

    def addWallet(self, wallet: Wallet):
        """Přidání uživatele do BlockChainu"""
        self.wallets.append(wallet)

    def isChainValid(self) -> bool:
        for block in self.chain:
            if (
                str(
                    sha256(
                        (
                            str(block.data)
                            + block.nonce
                            + block.previousHash
                            + block.timestamp
                        ).encode("utf-8")
                    ).hexdigest()
                )
                != block.hash
            ):
                return False
        return True

    def uploadMinedBlock(self, block: Block) -> bool:
        """Finalizování transakce, nahraje blok do blockchainu, pokud se jedná o validní vytěžený blok."""
        self.chain.append(block)
        if not self.isChainValid():
            self.chain.remove(block)
            return False
        for transaction in block.data:
            outs = transaction.outputs
            wal2 = None
            for wallet in self.wallets:
                if wallet.name == transaction.reciepent:
                    wal2 = wallet
            if wal2:
                wal2.UTXOs.append(TransactionInput(outs[1]))
        return True

    def makeBlock(self):
        """Vytvoření bloku v blockchainu, zařadí se do něj dosud nezařazené transakce."""
        block = Block(self.unminedTransactions, self.chain[-1].hash)
        self.unminedTransactions = []
        return block

    def addTransaction(self, transaction: Transaction):
        """Přídání transakce do blockchainu. Použijeme ji při iniciaci BlockChainu, obejde neexistenci odesilatele."""
        self.unminedTransactions.append(transaction)

    def addTransaction(self, sender: str, receipent: str, value: float):
        """Přetížená metoda, kterou budeme dále používat."""
        wal1 = None
        wal2 = None
        for wallet in self.wallets:
            if wallet.name == sender:
                wal1 = wallet
            if wallet.name == receipent:
                wal2 = wallet
        if wal1 and wal2:
            self.unminedTransactions.append(wal1.sendFunds(wal2, value))
        else:
            print("Chyba při hledání peněženek.")

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


if __name__ == "__main__":
    difficulty = 5
    Block.configDifficulty(difficulty)
    # change = False
    print(f"Obtížnost nastavena na {difficulty}.")

    blockchain = BlockChain()
    blockchain.addWallet(Wallet("Alice"))
    blockchain.addWallet(Wallet("Bob"))
    blockchain.addWallet(Wallet("Thanos"))

    block = Block(
        [
            Transaction(
                "0", "Alice", 100, [TransactionInput(TransactionOutput("0", 100, "0"))]
            )
        ],
        previousHash="0",
    )
    print("Těžím inicializační block...")
    ref = perf_counter()
    blockchain.uploadMinedBlock(block.mineBlock())
    print(f"Inicializační blok vytěžen za {perf_counter() - ref : .2f} sekund.")

    blockchain.addTransaction("Alice", "Bob", 30)
    blockchain.addTransaction("Alice", "Thanos", 12)
    blockchain.addTransaction("Alice", "Thanos", 5)
    print("Těžím první block...")
    ref = perf_counter()
    blockchain.uploadMinedBlock(blockchain.makeBlock().mineBlock())
    print(f"První block vytěžen za {perf_counter() - ref : .2f} sekund.")

    blockchain.addTransaction("Bob", "Thanos", 5)
    blockchain.addTransaction("Alice", "Thanos", 3)
    print("Těžím druhý block...")
    ref = perf_counter()
    blockchain.uploadMinedBlock(blockchain.makeBlock().mineBlock())
    print(f"Druhý block vytěžen za {perf_counter() - ref : .2f} sekund.")

    print(blockchain.toJSON())

    print("Kontrola Blockchainu: " + str(blockchain.isChainValid()))
