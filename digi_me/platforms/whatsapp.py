"""
WhatsApp Web Platform Integration
================================

Handles WhatsApp Web automation using Selenium WebDriver for message monitoring
and response automation.
"""

import asyncio
import logging
import os
import random
import shutil
import time
import uuid
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from ..platforms.base import PlatformBase

logger = logging.getLogger(__name__)


class WhatsAppPlatform(PlatformBase):
    """
    WhatsApp Web platform integration for the digital clone.
    
    This class handles:
    - Browser automation for WhatsApp Web
    - Message monitoring and detection
    - Automated response sending
    - Session persistence
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize WhatsApp platform with configuration."""
        super().__init__("whatsapp", config)
        
        # Configuration
        self.base_chrome_profile_path = config.get('chrome_profile_path', './chrome_profile')
        self.chrome_profile_path = None  # Will be set to unique path during setup
        self.headless = config.get('headless', False)
        self.response_delay = config.get('response_delay', (2, 5))  # Random delay range
        self.scan_interval = config.get('scan_interval', 3)  # Seconds between message checks
        self.auto_mark_read = config.get('auto_mark_read', True)
        
        # Browser components
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        
        # State management
        self.last_processed_messages: Dict[str, str] = {}  # contact -> last_message_id
        self.is_logged_in = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # WhatsApp Web selectors (may need updates based on WhatsApp changes)
        self.selectors = {
            'qr_code': '[data-testid="qr-code"]',
            'chat_list': '[data-testid="chat-list"]',
            'chat_item': '[data-testid="list-item-"]',
            'message_input': '[data-testid="compose-text-input"]',
            'send_button': '[data-testid="compose-btn-send"]',
            'message_container': '[data-testid="conversation-panel-messages"]',
            'message_item': '[data-testid="msg-container"]',
            'contact_name': '[data-testid="conversation-panel-header-title"]',
            'unread_indicator': '[data-testid="unread-count"]'
        }
        
        logger.info("WhatsApp Platform initialized")
    
    async def start(self):
        """Start the WhatsApp platform."""
        try:
            logger.info("Starting WhatsApp Platform...")
            
            # Setup browser
            await self._setup_browser()
            
            # Navigate to WhatsApp Web
            logger.info("Navigating to WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com")
            
            # Wait for login
            await self._wait_for_login()
            
            if self.is_logged_in:
                logger.info("Successfully logged into WhatsApp Web")
                # Start monitoring messages
                self.monitoring_task = asyncio.create_task(self._monitor_messages())
                self.is_active = True
            else:
                raise Exception("Failed to login to WhatsApp Web")
                
        except Exception as e:
            logger.error(f"Failed to start WhatsApp Platform: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the WhatsApp platform."""
        logger.info("Stopping WhatsApp Platform...")
        self.is_active = False
        
        # Cancel monitoring task
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Close browser
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            finally:
                self.driver = None
        
        # Clean up profile directory
        await self._cleanup_profile_directory()
        
        logger.info("WhatsApp Platform stopped")
    
    async def send_message(self, recipient: str, message: str) -> bool:
        """
        Send a message to a specific recipient.
        
        Args:
            recipient: Phone number or contact name
            message: Message text to send
            
        Returns:
            True if message was sent successfully
        """
        if not self.is_active or not self.driver:
            logger.error("WhatsApp platform is not active")
            return False
        
        try:
            logger.info(f"Sending message to {recipient}")
            
            # Navigate to chat
            if not await self._navigate_to_chat(recipient):
                logger.error(f"Could not navigate to chat with {recipient}")
                return False
            
            # Wait for message input to be available
            message_input = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.selectors['message_input']))
            )
            
            # Type message
            message_input.clear()
            message_input.send_keys(message)
            
            # Add small delay to seem natural
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Send message
            send_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.selectors['send_button']))
            )
            send_button.click()
            
            logger.info(f"Message sent to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to {recipient}: {e}")
            return False
    
    async def _setup_browser(self):
        """Setup Chrome browser with appropriate options."""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Generate unique profile directory
                self._create_unique_profile_path()
                
                chrome_options = Options()
                
                # Use unique profile to avoid conflicts
                chrome_options.add_argument(f"--user-data-dir={self.chrome_profile_path}")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                if self.headless:
                    chrome_options.add_argument("--headless")
                    chrome_options.add_argument("--no-sandbox")
                    chrome_options.add_argument("--disable-dev-shm-usage")
                
                # Additional options for stability and conflict avoidance
                chrome_options.add_argument("--disable-notifications")
                chrome_options.add_argument("--disable-popup-blocking")
                chrome_options.add_argument("--disable-web-security")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-plugins")
                chrome_options.add_argument("--disable-background-timer-throttling")
                chrome_options.add_argument("--disable-backgrounding-occluded-windows")
                chrome_options.add_argument("--disable-renderer-backgrounding")
                
                # Force new session
                chrome_options.add_argument("--no-first-run")
                chrome_options.add_argument("--no-default-browser-check")
                
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.wait = WebDriverWait(self.driver, 30)
                logger.info(f"Browser setup completed with profile: {self.chrome_profile_path}")
                return
                
            except WebDriverException as e:
                retry_count += 1
                logger.warning(f"Browser setup attempt {retry_count} failed: {e}")
                
                if retry_count < max_retries:
                    # Clean up failed attempt
                    await self._cleanup_failed_browser_setup()
                    await asyncio.sleep(2)
                else:
                    logger.error(f"Failed to setup browser after {max_retries} attempts: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error during browser setup: {e}")
                raise
    
    async def _wait_for_login(self):
        """Wait for user to scan QR code and login."""
        logger.info("Waiting for WhatsApp Web login...")
        
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # Check if QR code is present
                qr_elements = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['qr_code'])
                
                if qr_elements:
                    logger.info("QR Code detected. Please scan with your phone...")
                    await asyncio.sleep(5)
                    continue
                
                # Check if chat list is loaded (indicates successful login)
                chat_list_elements = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['chat_list'])
                
                if chat_list_elements:
                    logger.info("Login successful - chat list detected")
                    self.is_logged_in = True
                    return
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.warning(f"Error checking login status: {e}")
                await asyncio.sleep(2)
        
        logger.error("Login timeout - failed to login within 5 minutes")
        self.is_logged_in = False
    
    async def _monitor_messages(self):
        """Monitor for new messages and process them."""
        logger.info("Starting message monitoring...")
        
        while self.is_active:
            try:
                await self._check_for_new_messages()
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                logger.error(f"Error in message monitoring: {e}")
                await asyncio.sleep(self.scan_interval * 2)  # Wait longer after error
    
    async def _check_for_new_messages(self):
        """Check for new unread messages."""
        try:
            # Find chats with unread messages
            unread_chats = self.driver.find_elements(
                By.CSS_SELECTOR, 
                f'{self.selectors["chat_item"]} {self.selectors["unread_indicator"]}'
            )
            
            for unread_chat in unread_chats:
                try:
                    # Navigate to the chat
                    chat_element = unread_chat.find_element(By.XPATH, '../..')
                    chat_element.click()
                    
                    await asyncio.sleep(1)  # Wait for chat to load
                    
                    # Get contact name
                    contact_name = await self._get_current_contact_name()
                    
                    # Get new messages
                    new_messages = await self._get_new_messages(contact_name)
                    
                    # Process each new message
                    for message_data in new_messages:
                        await self._process_incoming_message(contact_name, message_data)
                    
                    # Mark as read if configured
                    if self.auto_mark_read:
                        await self._mark_chat_as_read()
                        
                except Exception as e:
                    logger.error(f"Error processing unread chat: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error checking for new messages: {e}")
    
    async def _get_current_contact_name(self) -> str:
        """Get the name of the currently open chat."""
        try:
            contact_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['contact_name']))
            )
            return contact_element.text.strip()
        except:
            return "Unknown"
    
    async def _get_new_messages(self, contact_name: str) -> List[Dict[str, Any]]:
        """Get new messages from the current chat."""
        new_messages = []
        
        try:
            # Get all message elements
            message_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                self.selectors['message_item']
            )
            
            # Process only recent messages (last few to avoid reprocessing old ones)
            recent_messages = message_elements[-10:] if len(message_elements) > 10 else message_elements
            
            for msg_element in recent_messages:
                try:
                    # Check if message is incoming (not sent by us)
                    if await self._is_incoming_message(msg_element):
                        message_id = msg_element.get_attribute('data-id') or str(time.time())
                        
                        # Check if we've already processed this message
                        if contact_name in self.last_processed_messages:
                            if self.last_processed_messages[contact_name] == message_id:
                                continue
                        
                        # Extract message content
                        message_content = await self._extract_message_content(msg_element)
                        
                        if message_content:
                            new_messages.append({
                                'id': message_id,
                                'content': message_content,
                                'timestamp': datetime.now(),
                                'sender': contact_name
                            })
                            
                            # Update last processed message
                            self.last_processed_messages[contact_name] = message_id
                
                except Exception as e:
                    logger.warning(f"Error processing message element: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error getting new messages: {e}")
        
        return new_messages
    
    async def _is_incoming_message(self, message_element) -> bool:
        """Check if a message is incoming (not sent by us)."""
        try:
            # WhatsApp uses different classes for incoming vs outgoing messages
            # This is a simplified check - may need refinement
            class_attr = message_element.get_attribute('class') or ''
            return 'message-in' in class_attr or not ('message-out' in class_attr)
        except:
            return True  # Default to treating as incoming
    
    async def _extract_message_content(self, message_element) -> Optional[str]:
        """Extract text content from a message element."""
        try:
            # Try different selectors for message text
            text_selectors = [
                '[data-testid="msg-text"]',
                '.copyable-text',
                '[dir="ltr"]',
                '.selectable-text'
            ]
            
            for selector in text_selectors:
                try:
                    text_element = message_element.find_element(By.CSS_SELECTOR, selector)
                    text = text_element.text.strip()
                    if text:
                        return text
                except NoSuchElementException:
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting message content: {e}")
            return None
    
    async def _process_incoming_message(self, sender: str, message_data: Dict[str, Any]):
        """Process an incoming message through the digital clone."""
        try:
            logger.info(f"Processing message from {sender}: {message_data['content'][:50]}...")
            
            # Prepare message data for the clone
            clone_message_data = {
                'sender': sender,
                'content': message_data['content'],
                'timestamp': message_data['timestamp'],
                'platform': 'whatsapp',
                'context': {
                    'message_id': message_data['id']
                }
            }
            
            # Process through digital clone
            if self.clone_reference:
                response = await self.clone_reference.process_message('whatsapp', clone_message_data)
                
                if response:
                    # Add natural delay before responding
                    delay = random.uniform(*self.response_delay)
                    logger.info(f"Waiting {delay:.1f} seconds before responding...")
                    await asyncio.sleep(delay)
                    
                    # Send response
                    success = await self.send_message(sender, response)
                    if success:
                        logger.info(f"Response sent to {sender}")
                    else:
                        logger.error(f"Failed to send response to {sender}")
            
        except Exception as e:
            logger.error(f"Error processing incoming message: {e}")
    
    async def _navigate_to_chat(self, recipient: str) -> bool:
        """Navigate to a specific chat."""
        try:
            # For phone numbers, use direct URL
            if recipient.startswith('+') or recipient.isdigit():
                url = f"https://web.whatsapp.com/send?phone={recipient.replace('+', '')}"
                self.driver.get(url)
                await asyncio.sleep(3)
                return True
            
            # For contact names, search in chat list
            # This is a simplified implementation
            search_box = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="chat-list-search"]')
            search_box.clear()
            search_box.send_keys(recipient)
            await asyncio.sleep(2)
            
            # Click on first result
            first_result = self.driver.find_element(By.CSS_SELECTOR, f'{self.selectors["chat_item"]}:first-child')
            first_result.click()
            await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to chat {recipient}: {e}")
            return False
    
    async def _mark_chat_as_read(self):
        """Mark the current chat as read."""
        try:
            # Scroll to bottom to mark as read
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", 
                                     self.driver.find_element(By.CSS_SELECTOR, self.selectors['message_container']))
        except Exception as e:
            logger.warning(f"Could not mark chat as read: {e}")
    
    def _create_unique_profile_path(self):
        """Create a unique Chrome profile directory path."""
        try:
            # Create base directory if it doesn't exist
            base_path = Path(self.base_chrome_profile_path)
            base_path.mkdir(parents=True, exist_ok=True)
            
            # Generate unique profile directory
            unique_id = f"{int(time.time())}_{str(uuid.uuid4())[:8]}"
            self.chrome_profile_path = str(base_path / f"session_{unique_id}")
            
            # If base profile exists, copy it to preserve login data
            if (base_path / "Default").exists():
                logger.info("Copying existing Chrome profile data...")
                shutil.copytree(str(base_path), self.chrome_profile_path, dirs_exist_ok=True)
            else:
                # Create the directory
                Path(self.chrome_profile_path).mkdir(parents=True, exist_ok=True)
                
            logger.info(f"Using Chrome profile: {self.chrome_profile_path}")
            
        except Exception as e:
            logger.warning(f"Could not create unique profile path: {e}, using default")
            self.chrome_profile_path = str(Path(self.base_chrome_profile_path) / "default")
    
    async def _cleanup_failed_browser_setup(self):
        """Clean up after a failed browser setup attempt."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                
            # Remove the failed profile directory
            if self.chrome_profile_path and Path(self.chrome_profile_path).exists():
                shutil.rmtree(self.chrome_profile_path, ignore_errors=True)
                logger.info(f"Cleaned up failed profile: {self.chrome_profile_path}")
                
        except Exception as e:
            logger.warning(f"Error during cleanup of failed browser setup: {e}")
    
    async def _cleanup_profile_directory(self):
        """Clean up the Chrome profile directory."""
        try:
            if not self.chrome_profile_path or self.chrome_profile_path == self.base_chrome_profile_path:
                return
                
            profile_path = Path(self.chrome_profile_path)
            if profile_path.exists() and "session_" in str(profile_path):
                # Save user data back to base profile if needed
                await self._save_profile_data()
                
                # Remove temporary session directory
                shutil.rmtree(str(profile_path), ignore_errors=True)
                logger.info(f"Cleaned up Chrome profile: {self.chrome_profile_path}")
                
        except Exception as e:
            logger.warning(f"Error cleaning up profile directory: {e}")
    
    async def _save_profile_data(self):
        """Save important profile data back to base profile."""
        try:
            if not self.chrome_profile_path:
                return
                
            source_path = Path(self.chrome_profile_path)
            base_path = Path(self.base_chrome_profile_path)
            
            # Files to preserve for future sessions
            important_files = [
                "Default/Local Storage",
                "Default/Session Storage", 
                "Default/IndexedDB",
                "Default/Cookies",
                "Default/Login Data",
                "Default/Preferences"
            ]
            
            base_path.mkdir(parents=True, exist_ok=True)
            
            for file_path in important_files:
                source = source_path / file_path
                target = base_path / file_path
                
                if source.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if source.is_dir():
                        if target.exists():
                            shutil.rmtree(str(target))
                        shutil.copytree(str(source), str(target))
                    else:
                        shutil.copy2(str(source), str(target))
                        
            logger.info("Saved Chrome profile data for future sessions")
            
        except Exception as e:
            logger.warning(f"Error saving profile data: {e}")
    
    def get_platform_status(self) -> Dict[str, Any]:
        """Get current platform status."""
        return {
            'is_active': self.is_active,
            'is_logged_in': self.is_logged_in,
            'browser_active': self.driver is not None,
            'monitoring_active': self.monitoring_task is not None and not self.monitoring_task.done(),
            'processed_contacts': len(self.last_processed_messages)
        }


