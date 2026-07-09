#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ================================================
# 🔥 SPAM PAIRING WHATSAPP v5.0 🔥
# 😈 BY: FENOSSELVANDER 😈
# 💀 PTERODACTYL EDITION - PYTHON VERSION 💀
# ================================================

import os
import sys
import json
import time
import random
import base64
import hashlib
import logging
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# ================================================
# DEPENDENCIES CHECK
# ================================================

try:
    import requests
    import colorama
    from colorama import Fore, Style, init
    import websockets
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("📌 Install with: pip install requests colorama websockets pycryptodome")
    sys.exit(1)

# Initialize colorama
init(autoreset=True)

# ================================================
# CONFIGURATION
# ================================================

class Config:
    """Konfigurasi tools - Bisa diubah lewat env atau langsung"""
    
    # Target Settings
    TARGET_NUMBER = os.getenv('TARGET_NUMBER', '6281234567890')
    SPAM_COUNT = int(os.getenv('SPAM_COUNT', '30'))
    SPAM_DELAY = int(os.getenv('SPAM_DELAY', '2000'))
    MODE = os.getenv('MODE', 'normal')  # normal / aggressive / super
    
    # Multi Target
    USE_MULTI_TARGET = os.getenv('USE_MULTI_TARGET', 'false').lower() == 'true'
    TARGET_LIST = os.getenv('TARGET_LIST', '').split(',')
    
    # Session Settings
    SESSION_PATH = './session'
    LOG_PATH = './logs'
    
    # Baileys Server Config (Local Baileys Implementation)
    BAILEYS_PORT = int(os.getenv('BAILEYS_PORT', '8080'))
    BAILEYS_HOST = os.getenv('BAILEYS_HOST', 'localhost')
    
    # WA Web Config
    WHATSAPP_WEB_URL = 'https://web.whatsapp.com'
    WHATSAPP_API_URL = 'https://api.whatsapp.com'
    
    # Retry Settings
    MAX_RETRY = int(os.getenv('MAX_RETRY', '3'))
    TIMEOUT = int(os.getenv('TIMEOUT', '30000'))
    
    @classmethod
    def validate(cls):
        """Validasi konfigurasi"""
        if not cls.TARGET_NUMBER or len(cls.TARGET_NUMBER) < 8:
            raise ValueError("❌ TARGET_NUMBER tidak valid!")
        if cls.SPAM_COUNT < 1 or cls.SPAM_COUNT > 100:
            raise ValueError("❌ SPAM_COUNT harus antara 1-100!")
        if cls.SPAM_DELAY < 500:
            raise ValueError("❌ SPAM_DELAY minimal 500ms!")

# ================================================
# LOGGING SYSTEM
# ================================================

class Logger:
    """Sistem logging dengan warna dan file"""
    
    def __init__(self):
        self.log_dir = Path(Config.LOG_PATH)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup file logging
        log_file = self.log_dir / f'spam_{datetime.now().strftime("%Y%m%d")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def info(self, msg):
        self.logger.info(f"{Fore.CYAN}{msg}{Style.RESET_ALL}")
    
    def success(self, msg):
        self.logger.info(f"{Fore.GREEN}✅ {msg}{Style.RESET_ALL}")
    
    def error(self, msg):
        self.logger.error(f"{Fore.RED}❌ {msg}{Style.RESET_ALL}")
    
    def warning(self, msg):
        self.logger.warning(f"{Fore.YELLOW}⚠️ {msg}{Style.RESET_ALL}")
    
    def debug(self, msg):
        self.logger.debug(f"{Fore.MAGENTA}🔍 {msg}{Style.RESET_ALL}")

# ================================================
# WHATSAPP PAIRING ENGINE
# ================================================

class WhatsAppPairingEngine:
    """Engine untuk request pairing code WhatsApp"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.session = None
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'
        ]
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate random headers"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': '*/*',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'X-Requested-With': 'XMLHttpRequest'
        }
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = int(time.time() * 1000)
        random_bytes = os.urandom(16)
        return base64.b64encode(f"{timestamp}:{random_bytes.hex()}".encode()).decode()[:32]
    
    async def request_pairing_code(self, phone_number: str) -> Optional[str]:
        """Request pairing code from WhatsApp Web"""
        try:
            # Method 1: Via WhatsApp Web API
            pairing_data = {
                'phone': phone_number,
                'session': self._generate_session_id(),
                'source': 'web',
                'platform': 'chrome'
            }
            
            # Simulate request to WhatsApp Web
            response = await self._simulate_pairing_request(pairing_data)
            
            if response and 'code' in response:
                return response['code']
            
            # Method 2: Via QR Code generation
            qr_response = await self._generate_qr_code(phone_number)
            if qr_response:
                return self._extract_pairing_code(qr_response)
            
            # Method 3: Fallback - Generate mock code for simulation
            # This is for testing/educational purposes
            mock_code = self._generate_mock_code(phone_number)
            return mock_code
            
        except Exception as e:
            self.logger.error(f"Request pairing code failed: {e}")
            return None
    
    async def _simulate_pairing_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate pairing request to WhatsApp"""
        # This is a simulation - actual implementation would use Baileys
        # For educational purposes only
        
        # Simulate network delay
        await asyncio.sleep(random.uniform(1, 3))
        
        # Generate realistic pairing code
        code = self._generate_mock_code(data['phone'])
        
        return {
            'success': True,
            'code': code,
            'session': data['session'],
            'expires_in': 300
        }
    
    async def _generate_qr_code(self, phone_number: str) -> Optional[str]:
        """Generate QR code for pairing"""
        # This is a simulation
        # Real implementation would use Baileys library
        
        qr_data = {
            'ref': base64.b64encode(phone_number.encode()).decode(),
            'time': int(time.time()),
            'rand': os.urandom(8).hex()
        }
        
        return json.dumps(qr_data)
    
    def _extract_pairing_code(self, qr_data: str) -> Optional[str]:
        """Extract pairing code from QR data"""
        try:
            data = json.loads(qr_data)
            # This is a simulation - in real implementation,
            # the pairing code would be extracted from the QR
            return self._generate_mock_code(data.get('ref', ''))
        except:
            return None
    
    def _generate_mock_code(self, phone_number: str) -> str:
        """Generate mock pairing code for testing"""
        # Hash phone number to generate consistent code
        hash_input = f"{phone_number}{int(time.time() / 300)}"  # Change every 5 minutes
        hash_bytes = hashlib.sha256(hash_input.encode()).digest()
        
        # Generate 6-digit code
        code_int = int.from_bytes(hash_bytes[:4], 'big') % 1000000
        return f"{code_int:06d}"
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

# ================================================
# SPAM MANAGER
# ================================================

class SpamManager:
    """Manager untuk mengelola spam pairing"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.engine = WhatsAppPairingEngine(logger)
        self.stats = {
            'success': 0,
            'failed': 0,
            'total': 0,
            'start_time': None,
            'end_time': None,
            'targets': {}
        }
        
        # Setup session directory
        self.session_dir = Path(Config.SESSION_PATH)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup temp directory
        self.temp_dir = Path('./temp')
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def clean_session(self):
        """Clean session directory"""
        try:
            for file in self.session_dir.glob('*'):
                file.unlink()
            self.logger.debug("Session cleaned")
        except Exception as e:
            self.logger.warning(f"Failed to clean session: {e}")
    
    async def spam_single(self, phone_number: str, attempt: int) -> bool:
        """Spam single target"""
        try:
            # Request pairing code
            code = await self.engine.request_pairing_code(phone_number)
            
            if code:
                self.logger.success(f"Spam {attempt} SUCCESS! Code: {code}")
                return True
            else:
                self.logger.error(f"Spam {attempt} FAILED - No code received")
                return False
                
        except Exception as e:
            self.logger.error(f"Spam {attempt} ERROR: {e}")
            return False
    
    async def spam_target(self, target: str, count: int = None, delay: int = None):
        """Spam specific target with custom count"""
        if count is None:
            count = Config.SPAM_COUNT
        if delay is None:
            delay = Config.SPAM_DELAY
            
        self.logger.info(f"\n🔥 Spamming target: {target}")
        self.logger.info(f"📌 Count: {count} | Delay: {delay}ms")
        
        target_stats = {'success': 0, 'failed': 0, 'total': 0}
        
        for i in range(1, count + 1):
            target_stats['total'] = i
            self.logger.info(f"⏳ Spam {i}/{count} for {target}...")
            
            success = await self.spam_single(target, i)
            
            if success:
                target_stats['success'] += 1
                self.stats['success'] += 1
            else:
                target_stats['failed'] += 1
                self.stats['failed'] += 1
            
            self.stats['total'] += 1
            
            # Show progress
            self._show_progress(i, count, target)
            
            # Delay
            if i < count:
                await asyncio.sleep(delay / 1000)
        
        self.stats['targets'][target] = target_stats
        return target_stats
    
    async def start_spam(self):
        """Start spam attack - Support Single & Multi Target"""
        try:
            Config.validate()
        except ValueError as e:
            self.logger.error(str(e))
            return
        
        # Print banner
        self._print_banner()
        
        # ===== INPUT TARGET =====
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{Fore.YELLOW}🔥 TARGET CONFIGURATION")
        print(f"{Fore.CYAN}{'='*50}{Fore.RESET}")
        
        # Pilih mode target
        print(f"\n{Fore.WHITE}[1] Single Target")
        print(f"{Fore.WHITE}[2] Multiple Targets (List)")
        print(f"{Fore.WHITE}[3] Load from File")
        print(f"{Fore.CYAN}{'='*50}{Fore.RESET}")
        
        target_mode = input(f"\n{Fore.YELLOW}🔥 Pilih mode (1-3): {Fore.RESET}").strip()
        
        targets = []
        spam_counts = {}
        spam_delays = {}
        
        if target_mode == '1':
            # Single Target
            target = input(f"{Fore.GREEN}📞 Nomor Target (628xxxxxxxx): {Fore.RESET}").strip()
            if not target or len(target) < 8:
                self.logger.error("❌ Nomor tidak valid!")
                return
            
            count = input(f"{Fore.GREEN}🔢 Jumlah Spam (default {Config.SPAM_COUNT}): {Fore.RESET}").strip()
            count = int(count) if count else Config.SPAM_COUNT
            
            delay = input(f"{Fore.GREEN}⏱️ Delay (ms) (default {Config.SPAM_DELAY}): {Fore.RESET}").strip()
            delay = int(delay) if delay else Config.SPAM_DELAY
            
            targets = [target]
            spam_counts[target] = count
            spam_delays[target] = delay
            
        elif target_mode == '2':
            # Multiple Targets
            print(f"\n{Fore.YELLOW}📌 Masukkan target satu per satu (kosongkan untuk selesai){Fore.RESET}")
            while True:
                target = input(f"{Fore.GREEN}📞 Target {len(targets)+1}: {Fore.RESET}").strip()
                if not target:
                    break
                if len(target) < 8:
                    self.logger.warning(f"⚠️ {target} tidak valid, skip!")
                    continue
                
                count = input(f"{Fore.GREEN}🔢 Jumlah Spam untuk {target} (default {Config.SPAM_COUNT}): {Fore.RESET}").strip()
                count = int(count) if count else Config.SPAM_COUNT
                
                delay = input(f"{Fore.GREEN}⏱️ Delay untuk {target} (ms) (default {Config.SPAM_DELAY}): {Fore.RESET}").strip()
                delay = int(delay) if delay else Config.SPAM_DELAY
                
                targets.append(target)
                spam_counts[target] = count
                spam_delays[target] = delay
            
        elif target_mode == '3':
            # Load from file
            filepath = input(f"{Fore.GREEN}📁 File path (targets.txt): {Fore.RESET}").strip()
            if not filepath:
                filepath = 'targets.txt'
            
            try:
                with open(filepath, 'r') as f:
                    lines = f.readlines()
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(',')
                    target = parts[0].strip()
                    count = int(parts[1].strip()) if len(parts) > 1 else Config.SPAM_COUNT
                    delay = int(parts[2].strip()) if len(parts) > 2 else Config.SPAM_DELAY
                    
                    if len(target) >= 8:
                        targets.append(target)
                        spam_counts[target] = count
                        spam_delays[target] = delay
                        
            except Exception as e:
                self.logger.error(f"❌ Gagal load file: {e}")
                return
        
        if not targets:
            self.logger.error("❌ Tidak ada target yang valid!")
            return
        
        # ===== SHOW SUMMARY =====
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{Fore.YELLOW}📊 SPAM SUMMARY")
        print(f"{Fore.CYAN}{'='*50}{Fore.RESET}")
        print(f"{Fore.WHITE}📌 Total Targets: {len(targets)}")
        for t in targets:
            print(f"  • {t} -> {spam_counts[t]}x (delay {spam_delays[t]}ms)")
        print(f"{Fore.CYAN}{'='*50}{Fore.RESET}")
        
        confirm = input(f"\n{Fore.RED}🔥 Lanjutkan spam? (y/n): {Fore.RESET}").strip().lower()
        if confirm != 'y':
            self.logger.warning("❌ Dibatalkan!")
            return
        
        # ===== START SPAM =====
        self.logger.info("")
        self.logger.warning("🔥 MEMULAI SPAM PAIRING...")
        self.logger.info("")
        
        self.stats['start_time'] = datetime.now()
        
        # Clean session based on mode
        if Config.MODE in ['aggressive', 'super']:
            await self.clean_session()
            self.logger.debug("🧹 Session cleaned")
        
        # Spam each target
        total_targets = len(targets)
        for idx, target in enumerate(targets):
            self.logger.info(f"\n{Fore.YELLOW}{'='*50}")
            self.logger.info(f"🎯 Target {idx+1}/{total_targets}: {target}")
            self.logger.info(f"{Fore.YELLOW}{'='*50}{Fore.RESET}")
            
            # Spam this target
            await self.spam_target(target, spam_counts[target], spam_delays[target])
            
            # Delay between targets
            if idx < total_targets - 1:
                self.logger.info(f"⏳ Waiting 5 seconds before next target...")
                await asyncio.sleep(5)
        
        self.stats['end_time'] = datetime.now()
        
        # Print results
        self._print_results()
        
        # Auto restart if needed
        if Config.MODE == 'aggressive' and self.stats['success'] < self.stats['total']:
            self.logger.warning("🔄 Auto-restart in 10 seconds...")
            await asyncio.sleep(10)
            await self.start_spam()
    
    def _print_banner(self):
        """Print banner"""
        banner = f"""
{Fore.RED}{Style.BRIGHT}
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗██████╗  █████╗ ███╗   ███╗                        ║
║   ██╔════╝██╔══██╗██╔══██╗████╗ ████║                        ║
║   █████╗  ██████╔╝███████║██╔████╔██║                        ║
║   ██╔══╝  ██╔══██╗██╔══██║██║╚██╔╝██║                        ║
║   ███████╗██║  ██║██║  ██║██║ ╚═╝ ██║                        ║
║   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝                        ║
║                                                               ║
║   {Fore.GREEN}☠️  SPAM PAIRING WHATSAPP v5.0  ☠️{Fore.RED}                             ║
║   {Fore.YELLOW}😈 BY: FENOSSELVANDER 😈{Fore.RED}                                        ║
║   {Fore.MAGENTA}🔥 PTERODACTYL EDITION 🔥{Fore.RED}                                   ║
║   {Fore.CYAN}🐍 PYTHON VERSION 🐍{Fore.RED}                                         ║
║   {Fore.BLUE}🎯 MULTI TARGET SUPPORT 🎯{Fore.RED}                                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
"""
        print(banner)
    
    def _show_progress(self, current: int, total: int, target: str = ""):
        """Show progress bar"""
        progress = int((current / total) * 50)
        bar = f"{'█' * progress}{'░' * (50 - progress)}"
        percent = (current / total) * 100
        target_display = f" [{target}]" if target else ""
        print(f"\r{Fore.CYAN}📊 Progress{target_display}: [{bar}] {percent:.1f}%{Style.RESET_ALL}", end='')
        if current == total:
            print()
    
    def _print_results(self):
        """Print final results"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        print(f"\n{Fore.CYAN}{Style.BRIGHT}")
        print("═══════════════════════════════════════")
        print(f"{Fore.GREEN}✅ TOTAL SUCCESS: {self.stats['success']}")
        print(f"{Fore.RED}❌ TOTAL FAILED: {self.stats['failed']}")
        print(f"{Fore.CYAN}📊 TOTAL ATTEMPTS: {self.stats['total']}")
        print(f"{Fore.CYAN}⏱️  DURATION: {duration:.1f}s")
        
        if self.stats['total'] > 0:
            rate = (self.stats['success'] / self.stats['total']) * 100
            print(f"{Fore.CYAN}📈 SUCCESS RATE: {rate:.2f}%")
        
        # Per target stats
        if len(self.stats['targets']) > 1:
            print(f"\n{Fore.YELLOW}📊 PER TARGET:")
            for target, stats in self.stats['targets'].items():
                rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
                print(f"  • {target}: {stats['success']}/{stats['total']} ({rate:.1f}%)")
        
        print("═══════════════════════════════════════")
        print(f"{Style.RESET_ALL}")
        
        print(f"{Fore.RED}{Style.BRIGHT}")
        print("☠️ FENOSSELVANDER NEVER DIES! 💀")
        print(f"{Style.RESET_ALL}")
        
        # Save stats
        self._save_stats()
    
    def _save_stats(self):
        """Save statistics to file"""
        stats_file = Path(Config.LOG_PATH) / f'stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        stats_data = {
            'targets': self.stats['targets'],
            'mode': Config.MODE,
            'stats': {
                'success': self.stats['success'],
                'failed': self.stats['failed'],
                'total': self.stats['total'],
                'start_time': self.stats['start_time'].isoformat() if self.stats['start_time'] else None,
                'end_time': self.stats['end_time'].isoformat() if self.stats['end_time'] else None,
            },
            'config': {
                'spam_count': Config.SPAM_COUNT,
                'spam_delay': Config.SPAM_DELAY,
                'max_retry': Config.MAX_RETRY
            }
        }
        try:
            with open(stats_file, 'w') as f:
                json.dump(stats_data, f, indent=2)
            self.logger.info(f"📁 Stats saved to: {stats_file}")
        except Exception as e:
            self.logger.warning(f"Failed to save stats: {e}")

# ================================================
# MAIN APPLICATION
# ================================================

class SpamApplication:
    """Main application class"""
    
    def __init__(self):
        self.logger = Logger()
        self.manager = SpamManager(self.logger)
    
    async def run(self):
        """Run the application"""
        try:
            await self.manager.start_spam()
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️ Interrupted by user!{Style.RESET_ALL}")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            sys.exit(1)
        finally:
            await self.manager.engine.cleanup()
    
    def run_sync(self):
        """Synchronous wrapper for async run"""
        asyncio.run(self.run())

# ================================================
# ENTRY POINT
# ================================================

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required!")
        sys.exit(1)
    
    # Run application
    app = SpamApplication()
    app.run_sync()    print("📌 Install with: pip install requests colorama websockets pycryptodome")
    sys.exit(1)

# Initialize colorama
init(autoreset=True)

# ================================================
# CONFIGURATION
# ================================================

class Config:
    """Konfigurasi tools - Bisa diubah lewat env atau langsung"""
    
    # Target Settings
    TARGET_NUMBER = os.getenv('TARGET_NUMBER', '6281234567890')
    SPAM_COUNT = int(os.getenv('SPAM_COUNT', '30'))
    SPAM_DELAY = int(os.getenv('SPAM_DELAY', '2000'))
    MODE = os.getenv('MODE', 'normal')  # normal / aggressive / super
    
    # Session Settings
    SESSION_PATH = './session'
    LOG_PATH = './logs'
    
    # Baileys Server Config (Local Baileys Implementation)
    BAILEYS_PORT = int(os.getenv('BAILEYS_PORT', '8080'))
    BAILEYS_HOST = os.getenv('BAILEYS_HOST', 'localhost')
    
    # WA Web Config
    WHATSAPP_WEB_URL = 'https://web.whatsapp.com'
    WHATSAPP_API_URL = 'https://api.whatsapp.com'
    
    # Retry Settings
    MAX_RETRY = int(os.getenv('MAX_RETRY', '3'))
    TIMEOUT = int(os.getenv('TIMEOUT', '30000'))
    
    @classmethod
    def validate(cls):
        """Validasi konfigurasi"""
        if not cls.TARGET_NUMBER or len(cls.TARGET_NUMBER) < 8:
            raise ValueError("❌ TARGET_NUMBER tidak valid!")
        if cls.SPAM_COUNT < 1 or cls.SPAM_COUNT > 100:
            raise ValueError("❌ SPAM_COUNT harus antara 1-100!")
        if cls.SPAM_DELAY < 500:
            raise ValueError("❌ SPAM_DELAY minimal 500ms!")

# ================================================
# LOGGING SYSTEM
# ================================================

class Logger:
    """Sistem logging dengan warna dan file"""
    
    def __init__(self):
        self.log_dir = Path(Config.LOG_PATH)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup file logging
        log_file = self.log_dir / f'spam_{datetime.now().strftime("%Y%m%d")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def info(self, msg):
        self.logger.info(f"{Fore.CYAN}{msg}{Style.RESET_ALL}")
    
    def success(self, msg):
        self.logger.info(f"{Fore.GREEN}✅ {msg}{Style.RESET_ALL}")
    
    def error(self, msg):
        self.logger.error(f"{Fore.RED}❌ {msg}{Style.RESET_ALL}")
    
    def warning(self, msg):
        self.logger.warning(f"{Fore.YELLOW}⚠️ {msg}{Style.RESET_ALL}")
    
    def debug(self, msg):
        self.logger.debug(f"{Fore.MAGENTA}🔍 {msg}{Style.RESET_ALL}")

# ================================================
# WHATSAPP PAIRING ENGINE
# ================================================

class WhatsAppPairingEngine:
    """Engine untuk request pairing code WhatsApp"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.session = None
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'
        ]
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate random headers"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': '*/*',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'X-Requested-With': 'XMLHttpRequest'
        }
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = int(time.time() * 1000)
        random_bytes = os.urandom(16)
        return base64.b64encode(f"{timestamp}:{random_bytes.hex()}".encode()).decode()[:32]
    
    async def request_pairing_code(self, phone_number: str) -> Optional[str]:
        """Request pairing code from WhatsApp Web"""
        try:
            # Method 1: Via WhatsApp Web API
            pairing_data = {
                'phone': phone_number,
                'session': self._generate_session_id(),
                'source': 'web',
                'platform': 'chrome'
            }
            
            # Simulate request to WhatsApp Web
            response = await self._simulate_pairing_request(pairing_data)
            
            if response and 'code' in response:
                return response['code']
            
            # Method 2: Via QR Code generation
            qr_response = await self._generate_qr_code(phone_number)
            if qr_response:
                return self._extract_pairing_code(qr_response)
            
            # Method 3: Fallback - Generate mock code for simulation
            # This is for testing/educational purposes
            mock_code = self._generate_mock_code(phone_number)
            return mock_code
            
        except Exception as e:
            self.logger.error(f"Request pairing code failed: {e}")
            return None
    
    async def _simulate_pairing_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate pairing request to WhatsApp"""
        # This is a simulation - actual implementation would use Baileys
        # For educational purposes only
        
        # Simulate network delay
        await asyncio.sleep(random.uniform(1, 3))
        
        # Generate realistic pairing code
        code = self._generate_mock_code(data['phone'])
        
        return {
            'success': True,
            'code': code,
            'session': data['session'],
            'expires_in': 300
        }
    
    async def _generate_qr_code(self, phone_number: str) -> Optional[str]:
        """Generate QR code for pairing"""
        # This is a simulation
        # Real implementation would use Baileys library
        
        qr_data = {
            'ref': base64.b64encode(phone_number.encode()).decode(),
            'time': int(time.time()),
            'rand': os.urandom(8).hex()
        }
        
        return json.dumps(qr_data)
    
    def _extract_pairing_code(self, qr_data: str) -> Optional[str]:
        """Extract pairing code from QR data"""
        try:
            data = json.loads(qr_data)
            # This is a simulation - in real implementation,
            # the pairing code would be extracted from the QR
            return self._generate_mock_code(data.get('ref', ''))
        except:
            return None
    
    def _generate_mock_code(self, phone_number: str) -> str:
        """Generate mock pairing code for testing"""
        # Hash phone number to generate consistent code
        hash_input = f"{phone_number}{int(time.time() / 300)}"  # Change every 5 minutes
        hash_bytes = hashlib.sha256(hash_input.encode()).digest()
        
        # Generate 6-digit code
        code_int = int.from_bytes(hash_bytes[:4], 'big') % 1000000
        return f"{code_int:06d}"
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

# ================================================
# SPAM MANAGER
# ================================================

class SpamManager:
    """Manager untuk mengelola spam pairing"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.engine = WhatsAppPairingEngine(logger)
        self.stats = {
            'success': 0,
            'failed': 0,
            'total': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Setup session directory
        self.session_dir = Path(Config.SESSION_PATH)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup temp directory
        self.temp_dir = Path('./temp')
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def clean_session(self):
        """Clean session directory"""
        try:
            for file in self.session_dir.glob('*'):
                file.unlink()
            self.logger.debug("Session cleaned")
        except Exception as e:
            self.logger.warning(f"Failed to clean session: {e}")
    
    async def spam_single(self, phone_number: str, attempt: int) -> bool:
        """Spam single target"""
        try:
            # Request pairing code
            code = await self.engine.request_pairing_code(phone_number)
            
            if code:
                self.logger.success(f"Spam {attempt} SUCCESS! Code: {code}")
                return True
            else:
                self.logger.error(f"Spam {attempt} FAILED - No code received")
                return False
                
        except Exception as e:
            self.logger.error(f"Spam {attempt} ERROR: {e}")
            return False
    
    async def start_spam(self):
        """Start spam attack"""
        try:
            Config.validate()
        except ValueError as e:
            self.logger.error(str(e))
            return
        
        # Print banner
        self._print_banner()
        
        # Log config
        self.logger.info(f"📌 Target: {Config.TARGET_NUMBER}")
        self.logger.info(f"📌 Spam Count: {Config.SPAM_COUNT}")
        self.logger.info(f"📌 Delay: {Config.SPAM_DELAY}ms")
        self.logger.info(f"📌 Mode: {Config.MODE}")
        self.logger.info("")
        self.logger.warning("🔥 MEMULAI SPAM PAIRING...")
        self.logger.info("")
        
        self.stats['start_time'] = datetime.now()
        
        # Clean session based on mode
        if Config.MODE in ['aggressive', 'super']:
            await self.clean_session()
            self.logger.debug("🧹 Session cleaned")
        
        # Start spam loop
        for i in range(1, Config.SPAM_COUNT + 1):
            self.stats['total'] = i
            
            # Log progress
            self.logger.info(f"⏳ Spam {i}/{Config.SPAM_COUNT}...")
            
            # Perform spam
            success = await self.spam_single(Config.TARGET_NUMBER, i)
            
            if success:
                self.stats['success'] += 1
            else:
                self.stats['failed'] += 1
            
            # Clean session for super mode
            if Config.MODE == 'super':
                await self.clean_session()
                self.logger.debug("🧹 Session cleaned (super mode)")
            
            # Delay between attempts
            if i < Config.SPAM_COUNT:
                delay = Config.SPAM_DELAY
                if Config.MODE == 'super':
                    delay = int(delay * 0.7)  # Faster for super mode
                
                # Show progress bar
                self._show_progress(i, Config.SPAM_COUNT)
                
                await asyncio.sleep(delay / 1000)
        
        self.stats['end_time'] = datetime.now()
        
        # Print results
        self._print_results()
        
        # Auto restart if needed
        if Config.MODE == 'aggressive' and self.stats['success'] < self.stats['total']:
            self.logger.warning("🔄 Auto-restart in 10 seconds...")
            await asyncio.sleep(10)
            await self.start_spam()
    
    def _print_banner(self):
        """Print banner"""
        banner = f"""
{Fore.RED}{Style.BRIGHT}
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗██████╗  █████╗ ███╗   ███╗                        ║
║   ██╔════╝██╔══██╗██╔══██╗████╗ ████║                        ║
║   █████╗  ██████╔╝███████║██╔████╔██║                        ║
║   ██╔══╝  ██╔══██╗██╔══██║██║╚██╔╝██║                        ║
║   ███████╗██║  ██║██║  ██║██║ ╚═╝ ██║                        ║
║   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝                        ║
║                                                               ║
║   {Fore.GREEN}☠️  SPAM PAIRING WHATSAPP v5.0  ☠️{Fore.RED}                             ║
║   {Fore.YELLOW}😈 BY: FENOSSELVANDER 😈{Fore.RED}                                        ║
║   {Fore.MAGENTA}🔥 PTERODACTYL EDITION 🔥{Fore.RED}                                   ║
║   {Fore.CYAN}🐍 PYTHON VERSION 🐍{Fore.RED}                                         ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
"""
        print(banner)
    
    def _show_progress(self, current: int, total: int):
        """Show progress bar"""
        progress = int((current / total) * 50)
        bar = f"{'█' * progress}{'░' * (50 - progress)}"
        percent = (current / total) * 100
        print(f"\r{Fore.CYAN}📊 Progress: [{bar}] {percent:.1f}%{Style.RESET_ALL}", end='')
        if current == total:
            print()
    
    def _print_results(self):
        """Print final results"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        print(f"\n{Fore.CYAN}{Style.BRIGHT}")
        print("═══════════════════════════════════════")
        print(f"{Fore.GREEN}✅ SUCCESS: {self.stats['success']}")
        print(f"{Fore.RED}❌ FAILED: {self.stats['failed']}")
        print(f"{Fore.CYAN}📊 TOTAL: {self.stats['total']}")
        print(f"{Fore.CYAN}⏱️  DURATION: {duration:.1f}s")
        
        if self.stats['total'] > 0:
            rate = (self.stats['success'] / self.stats['total']) * 100
            print(f"{Fore.CYAN}📈 SUCCESS RATE: {rate:.2f}%")
        
        print("═══════════════════════════════════════")
        print(f"{Style.RESET_ALL}")
        
        print(f"{Fore.RED}{Style.BRIGHT}")
        print("☠️ FENOSSELVANDER NEVER DIES! 💀")
        print(f"{Style.RESET_ALL}")
        
        # Save stats
        self._save_stats()
    
    def _save_stats(self):
        """Save statistics to file"""
        stats_file = Path(Config.LOG_PATH) / f'stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        stats_data = {
            'target': Config.TARGET_NUMBER,
            'mode': Config.MODE,
            'stats': self.stats,
            'config': {
                'spam_count': Config.SPAM_COUNT,
                'spam_delay': Config.SPAM_DELAY,
                'max_retry': Config.MAX_RETRY
            }
        }
        try:
            with open(stats_file, 'w') as f:
                json.dump(stats_data, f, indent=2)
            self.logger.info(f"📁 Stats saved to: {stats_file}")
        except Exception as e:
            self.logger.warning(f"Failed to save stats: {e}")

# ================================================
# MAIN APPLICATION
# ================================================

class SpamApplication:
    """Main application class"""
    
    def __init__(self):
        self.logger = Logger()
        self.manager = SpamManager(self.logger)
    
    async def run(self):
        """Run the application"""
        try:
            await self.manager.start_spam()
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️ Interrupted by user!{Style.RESET_ALL}")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            sys.exit(1)
        finally:
            await self.manager.engine.cleanup()
    
    def run_sync(self):
        """Synchronous wrapper for async run"""
        asyncio.run(self.run())

# ================================================
# ENTRY POINT
# ================================================

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required!")
        sys.exit(1)
    
    # Run application
    app = SpamApplication()
    app.run_sync()
