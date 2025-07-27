import os
import time
import requests
import json
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from mnemonic import Mnemonic
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from config import CONFIG

class SolanaRecovery:
    def __init__(self):
        self.mnemo = Mnemonic("english")
        self.client_rotation = CONFIG["rpc_endpoints"]
        self.current_rpc = 0
        self.executor = ThreadPoolExecutor(max_workers=CONFIG["max_workers"])
        self.cache = set()
        self.found_wallets = []
        self.attempts = 0
        self.start_time = time.time()
        self.running = True
        
    def _rotate_rpc(self):
        """Rotate RPC with connection testing"""
        for _ in range(len(self.client_rotation)):
            self.current_rpc = (self.current_rpc + 1) % len(self.client_rotation)
            endpoint = self.client_rotation[self.current_rpc]
            try:
                client = Client(endpoint, timeout=CONFIG["timeout"])
                client.get_epoch_info()  # Test connection
                return client
            except Exception as e:
                print(f"⚠️ RPC failed ({endpoint}): {str(e)}")
                continue
        raise Exception("All RPC endpoints failed")

    def notify_telegram(self, message):
        """Send notification to Telegram"""
        url = f"https://api.telegram.org/bot{CONFIG['telegram']['bot_token']}/sendMessage"
        try:
            requests.post(url, json={
                "chat_id": CONFIG["telegram"]["chat_id"],
                "text": message,
                "parse_mode": "HTML"
            }, timeout=10)
        except Exception as e:
            print(f"⚠️ Telegram error: {str(e)}")
    
    def send_stop_notification(self, reason="Manual stop"):
        """Send notification when bot stops"""
        elapsed = time.time() - self.start_time
        msg = (
            "🛑 BOT STOPPED\n\n"
            f"⏱️ Runtime: {elapsed/3600:.2f} hours\n"
            f"🔍 Total attempts: {self.attempts:,}\n"
            f"💰 Wallets found: {len(self.found_wallets)}\n"
            f"⚡ Average speed: {self.attempts/elapsed:.1f} seeds/sec\n"
            f"📌 Reason: {reason}"
        )
        self.notify_telegram(msg)
    
    def generate_seeds(self):
        """Generate seed phrases"""
        wordlist = self.mnemo.wordlist if CONFIG["bip39_wordlist"] else CONFIG["common_words"]
        
        while self.running:
            seed = [""] * 12
            for pos, word in CONFIG["known_words"].items():
                seed[pos] = word
            for i in range(12):
                if seed[i] == "":
                    seed[i] = np.random.choice(wordlist)
            yield ' '.join(seed)
    
    def _get_transaction_count(self, pubkey):
        """Check transaction count"""
        for url in CONFIG["explorers"]:
            try:
                res = requests.get(f"{url}{pubkey}", timeout=10).json()
                return res.get("txCount", 0)
            except:
                continue
        return 0
    
    def check_wallet(self, seed_phrase):
        """Check wallet balance and transactions"""
        if not self.running or seed_phrase in self.cache:
            return None, None, 0, 0
            
        self.cache.add(seed_phrase)
        try:
            seed_bytes = self.mnemo.to_seed(seed_phrase)
            keypair = Keypair.from_seed(seed_bytes[:32])
            pubkey = str(keypair.pubkey())
            
            tx_count = self._get_transaction_count(pubkey)
            if tx_count == 0:
                return None, None, 0, 0
                
            client = self._rotate_rpc()
            balance = client.get_balance(Pubkey.from_string(pubkey)).value / 10**9
            return seed_phrase, pubkey, balance, tx_count
            
        except Exception as e:
            print(f"⚠️ Error: {str(e)}")
            return None, None, 0, 0
    
    def run_continuous(self):
        """Main recovery loop"""
        self.notify_telegram(
            "🚀 BOT STARTED\n\n"
            f"🔍 Known words: {CONFIG['known_words']}\n"
            f"⚡ Workers: {CONFIG['max_workers']}\n"
            f"🔁 Mode: Continuous"
        )
        
        try:
            generator = self.generate_seeds()
            with tqdm(desc="Processing", unit=" seeds") as progress:
                while self.running:
                    batch = [next(generator) for _ in range(CONFIG["batch_size"])]
                    self.attempts += len(batch)
                    
                    futures = []
                    for seed in batch:
                        if not self.running:
                            break
                        futures.append(self.executor.submit(self.check_wallet, seed))
                    
                    for future in as_completed(futures):
                        if not self.running:
                            break
                        seed_phrase, pubkey, balance, tx_count = future.result()
                        if balance > 0 or (CONFIG["notify_empty_tx"] and tx_count > 0):
                            self._handle_found_wallet(seed_phrase, pubkey, balance, tx_count)
                    
                    progress.update(len(batch))
                    
                    if self.attempts % 5000 == 0:
                        self._report_progress()
                        
        except KeyboardInterrupt:
            self.running = False
            self.send_stop_notification("Manual interruption")
        except Exception as e:
            self.running = False
            self.send_stop_notification(f"Error: {str(e)}")
            raise
        finally:
            self.executor.shutdown(wait=False)
    
    def _handle_found_wallet(self, seed_phrase, pubkey, balance, tx_count):
        """Process found wallets"""
        wallet_data = {
            "seed": seed_phrase,
            "pubkey": pubkey,
            "balance": balance,
            "tx_count": tx_count,
            "timestamp": time.time()
        }
        self.found_wallets.append(wallet_data)
        
        msg = (
            "💰 WALLET FOUND\n\n"
            f"🔑 Pubkey: <code>{pubkey}</code>\n"
            f"🌱 Seed: <code>{seed_phrase}</code>\n"
            f"💎 Balance: {balance} SOL\n"
            f"📊 Transactions: {tx_count}"
        )
        self.notify_telegram(msg)
        
        with open("found_wallets.json", "a") as f:
            f.write(json.dumps(wallet_data) + "\n")
    
    def _report_progress(self):
        """Send progress report"""
        elapsed = time.time() - self.start_time
        msg = (
            "📊 PROGRESS REPORT\n\n"
            f"⏱️ Runtime: {elapsed/3600:.2f} hours\n"
            f"🔍 Attempts: {self.attempts:,}\n"
            f"💰 Found: {len(self.found_wallets)}\n"
            f"⚡ Speed: {self.attempts/elapsed:.1f} seeds/sec"
        )
        self.notify_telegram(msg)

if __name__ == "__main__":
    engine = SolanaRecovery()
    try:
        engine.run_continuous()
    except Exception as e:
        print(f"🔥 Critical error: {str(e)}")
    finally:
        # Ensure final notification is sent
        if hasattr(engine, 'running') and engine.running:
            engine.send_stop_notification("Unexpected termination")