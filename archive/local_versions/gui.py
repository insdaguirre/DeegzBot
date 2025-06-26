import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QTextEdit, QSpinBox, QDoubleSpinBox, QTabWidget,
                           QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from instagram_bot import InstagramBot
import json
import os
from datetime import datetime
import csv
from pathlib import Path

class InstagramAutomationGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.bot = None
        self.worker = None
        self.data_dir = self.setup_data_directory()

    def setup_data_directory(self):
        """Create and return the data directory path"""
        # Create a data directory in the same folder as the script
        data_dir = Path(os.path.dirname(os.path.abspath(__file__))) / 'instagram_data'
        data_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (data_dir / 'csv_exports').mkdir(exist_ok=True)
        (data_dir / 'logs').mkdir(exist_ok=True)
        
        return data_dir

    def get_log_path(self):
        """Get the path for the action log file"""
        return self.data_dir / 'logs' / 'action_log.json'

    def initUI(self):
        self.setWindowTitle('Instagram Automation')
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tabs
        tabs = QTabWidget()
        follow_tab = QWidget()
        unfollow_tab = QWidget()
        log_tab = QWidget()
        
        tabs.addTab(follow_tab, "Follow")
        tabs.addTab(unfollow_tab, "Unfollow")
        tabs.addTab(log_tab, "Log")
        
        # Set up Follow tab
        follow_layout = QVBoxLayout(follow_tab)
        
        # Credentials section
        cred_layout = QHBoxLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('Instagram Username')
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Instagram Password')
        self.password_input.setEchoMode(QLineEdit.Password)
        cred_layout.addWidget(self.username_input)
        cred_layout.addWidget(self.password_input)
        follow_layout.addLayout(cred_layout)

        # Target accounts section
        follow_layout.addWidget(QLabel('Target Accounts (one per line):'))
        self.accounts_input = QTextEdit()
        self.accounts_input.setPlaceholderText('Enter Instagram accounts to scrape followers from')
        follow_layout.addWidget(self.accounts_input)

        # Settings section for Follow
        settings_layout = QHBoxLayout()
        
        # Number of users to follow
        follow_count_layout = QVBoxLayout()
        follow_count_layout.addWidget(QLabel('Users to Follow per Account:'))
        self.follow_count = QSpinBox()
        self.follow_count.setRange(1, 1000)
        self.follow_count.setValue(50)
        follow_count_layout.addWidget(self.follow_count)
        settings_layout.addLayout(follow_count_layout)

        # Note about automatic delays
        delay_note = QLabel('ℹ️ Delays are automatically optimized for safety and speed')
        delay_note.setStyleSheet("color: #666; font-style: italic; font-size: 11px; padding: 5px;")
        settings_layout.addWidget(delay_note)

        follow_layout.addLayout(settings_layout)

        # Status log for Follow
        follow_layout.addWidget(QLabel('Status:'))
        self.follow_log_display = QTextEdit()
        self.follow_log_display.setReadOnly(True)
        follow_layout.addWidget(self.follow_log_display)

        # Follow control button
        self.follow_button = QPushButton('Start Following')
        self.follow_button.clicked.connect(lambda: self.start_automation('follow'))
        follow_layout.addWidget(self.follow_button)

        # Set up Unfollow tab
        unfollow_layout = QVBoxLayout(unfollow_tab)
        
        # CSV import section
        unfollow_layout.addWidget(QLabel('Import accounts to unfollow from CSV:'))
        
        # CSV import controls
        csv_import_layout = QHBoxLayout()
        self.csv_import_button = QPushButton('Import from CSV')
        self.csv_import_button.clicked.connect(self.import_csv)
        csv_import_layout.addWidget(self.csv_import_button)
        csv_import_layout.addStretch()
        unfollow_layout.addLayout(csv_import_layout)

        # Add label to show selected CSV file
        self.csv_file_label = QLabel('')
        self.csv_file_label.setWordWrap(True)  # Enable word wrap for long paths
        unfollow_layout.addWidget(self.csv_file_label)

        # Note about automatic delays
        unfollow_delay_note = QLabel('ℹ️ Delays are automatically optimized for speed and safety')
        unfollow_delay_note.setStyleSheet("color: #666; font-style: italic; font-size: 11px; padding: 5px;")
        unfollow_layout.addWidget(unfollow_delay_note)

        # Status log for Unfollow
        unfollow_layout.addWidget(QLabel('Status:'))
        self.unfollow_log_display = QTextEdit()
        self.unfollow_log_display.setReadOnly(True)
        unfollow_layout.addWidget(self.unfollow_log_display)

        # Unfollow control button
        self.unfollow_button = QPushButton('Start Unfollowing')
        self.unfollow_button.clicked.connect(lambda: self.start_automation('unfollow'))
        self.unfollow_button.setEnabled(False)  # Disable until CSV is imported
        unfollow_layout.addWidget(self.unfollow_button)

        # Set up Log tab
        log_layout = QVBoxLayout(log_tab)
        self.history_log = QTextEdit()
        self.history_log.setReadOnly(True)
        log_layout.addWidget(self.history_log)
        
        # Refresh log button
        refresh_button = QPushButton('Refresh Log')
        refresh_button.clicked.connect(self.refresh_log)
        log_layout.addWidget(refresh_button)

        # Add tabs to main layout
        layout.addWidget(tabs)

        self.load_settings()
        self.refresh_log()

    def log_action(self, action_type, accounts, timestamp=None):
        try:
            if timestamp is None:
                timestamp = datetime.now().isoformat()
                
            log_entry = {
                'timestamp': timestamp,
                'action': action_type,
                'accounts': accounts
            }
            
            log_path = self.get_log_path()
            
            # Load existing log
            if log_path.exists():
                with open(log_path, 'r') as f:
                    log = json.load(f)
            else:
                log = []
                
            # Add new entry
            log.append(log_entry)
            
            # Save updated log
            with open(log_path, 'w') as f:
                json.dump(log, f, indent=2)
                
        except Exception as e:
            print(f"Error saving log: {str(e)}")

    def refresh_log(self):
        try:
            log_path = self.get_log_path()
            if log_path.exists():
                with open(log_path, 'r') as f:
                    log = json.load(f)
                    
                # Clear current display
                self.history_log.clear()
                
                # Display each log entry
                for entry in log:
                    timestamp = entry['timestamp']
                    action = entry['action']
                    accounts = entry['accounts']
                    
                    self.history_log.append(f"=== {action.upper()} - {timestamp} ===")
                    self.history_log.append("Accounts:")
                    for account in accounts:
                        self.history_log.append(f"- {account}")
                    self.history_log.append("\n")
            else:
                self.history_log.setText("No action history found.")
                
        except Exception as e:
            self.history_log.setText(f"Error loading log: {str(e)}")

    def start_automation(self, action_type):
        if action_type == 'follow':
            if not self.username_input.text() or not self.password_input.text():
                QMessageBox.warning(self, 'Error', 'Please enter your Instagram credentials.')
                return

            target_accounts = [acc.strip() for acc in self.accounts_input.toPlainText().split('\n') if acc.strip()]
            if not target_accounts:
                QMessageBox.warning(self, 'Error', 'Please enter at least one target account.')
                return

            # Save settings
            self.save_settings()

            # Create bot instance for following (delays are now automatic)
            self.bot = InstagramBot(
                username=self.username_input.text(),
                password=self.password_input.text(),
                target_accounts=target_accounts,
                users_per_account=self.follow_count.value(),
                unfollow_delay=0  # Not used for following
            )

            # Start worker
            self.worker = BotWorker(self.bot, action_type)
            self.worker.log_signal.connect(lambda msg: self.log(msg, action_type))
            self.worker.finished.connect(lambda accounts: self.automation_finished(action_type, accounts))
            self.worker.start()

            # Update UI
            self.follow_button.setEnabled(False)
            
        elif action_type == 'unfollow':
            if not self.username_input.text() or not self.password_input.text():
                QMessageBox.warning(self, 'Error', 'Please enter your Instagram credentials.')
                return

            # Create bot instance for unfollowing (delays are now automatic)
            self.bot = InstagramBot(
                username=self.username_input.text(),
                password=self.password_input.text(),
                target_accounts=self.unfollow_accounts,  # Used as unfollow list
                users_per_account=0,  # Not used for unfollowing
                unfollow_delay=0  # Not used here
            )

            # Start worker
            self.worker = BotWorker(self.bot, action_type)
            self.worker.log_signal.connect(lambda msg: self.log(msg, action_type))
            self.worker.finished.connect(lambda accounts: self.automation_finished(action_type, accounts))
            self.worker.start()

            # Update UI
            self.unfollow_button.setEnabled(False)

    def log(self, message, action_type):
        if action_type == 'follow':
            self.follow_log_display.append(message)
        else:
            self.unfollow_log_display.append(message)

    def automation_finished(self, action_type, processed_accounts):
        if action_type == 'follow':
            self.follow_button.setEnabled(True)
            # Export followed users to CSV - ONE FILE PER BATCH
            if processed_accounts:
                self.log(f"🎉 Batch completed! Successfully processed {len(processed_accounts)} accounts", action_type)
                self.export_followed_users(processed_accounts)
                self.log(f"💾 CSV export completed - single batch file created", action_type)
        else:
            self.unfollow_button.setEnabled(True)
            if processed_accounts:
                self.log(f"🎉 Unfollow batch completed! Successfully processed {len(processed_accounts)} accounts", action_type)
            
        # Log the action
        self.log_action(action_type, processed_accounts)
        self.refresh_log()
        
        # Show completion message with path information
        if action_type == 'follow' and processed_accounts:
            csv_path = self.data_dir / 'csv_exports'
            QMessageBox.information(
                self, 
                'Complete', 
                f'✅ {action_type.capitalize()} operation completed!\n\n'
                f'📊 Processed: {len(processed_accounts)} accounts\n'
                f'💾 Single CSV file created (no more spam!)\n\n'
                f'CSV exports: {csv_path}\n'
                f'Log files: {self.data_dir / "logs"}'
            )
        else:
            QMessageBox.information(self, 'Complete', f'{action_type.capitalize()} operation completed.')

    def save_settings(self):
        settings = {
            'username': self.username_input.text(),
            'target_accounts': self.accounts_input.toPlainText(),
            'follow_count': self.follow_count.value(),
        }
        with open('settings.json', 'w') as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                    self.username_input.setText(settings.get('username', ''))
                    self.accounts_input.setText(settings.get('target_accounts', ''))
                    self.follow_count.setValue(settings.get('follow_count', 50))
        except:
            pass

    def import_csv(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if file_name:
            try:
                usernames = []
                invalid_usernames = []
                
                with open(file_name, 'r') as f:
                    reader = csv.reader(f)
                    for i, row in enumerate(reader):
                        if row:  # Skip empty rows
                            username = row[0].strip()
                            
                            # Skip common header names
                            if username.lower() in ['username', 'user', 'account', 'name', 'handle']:
                                continue
                            
                            # Basic username validation
                            if self.is_valid_username(username):
                                usernames.append(username)
                            else:
                                invalid_usernames.append(username)
                
                # Update the GUI
                self.csv_file_label.setText(f"Selected file: {file_name}")
                self.csv_file_label.setStyleSheet("color: green")
                self.unfollow_button.setEnabled(True)
                
                # Store the usernames
                self.unfollow_accounts = usernames
                
                # Log success and any issues
                self.log(f"✅ Successfully imported {len(usernames)} valid usernames from CSV", 'unfollow')
                
                if invalid_usernames:
                    self.log(f"⚠️ Skipped {len(invalid_usernames)} invalid usernames: {invalid_usernames[:5]}", 'unfollow')
                
            except Exception as e:
                self.csv_file_label.setText("Error importing file")
                self.csv_file_label.setStyleSheet("color: red")
                self.unfollow_button.setEnabled(False)
                self.log(f"❌ Error importing CSV: {str(e)}", 'unfollow')
        else:
            self.csv_file_label.setText("No file selected")
            self.csv_file_label.setStyleSheet("color: red")
            self.unfollow_button.setEnabled(False)

    def is_valid_username(self, username):
        """Check if username is valid for Instagram"""
        if not username or len(username) < 1:
            return False
        
        # Instagram usernames can only contain letters, numbers, periods, and underscores
        import re
        if not re.match(r'^[a-zA-Z0-9._]+$', username):
            return False
        
        # Must be between 1 and 30 characters
        if len(username) > 30:
            return False
        
        # Can't be just numbers or just periods
        if username.isdigit() or username.replace('.', '') == '':
            return False
        
        return True

    def export_followed_users(self, usernames):
        """Export followed users - automatic batch export (no dialog spam)"""
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Auto-save to csv_exports directory (no popup dialog)
            csv_dir = self.data_dir / 'csv_exports'
            csv_dir.mkdir(exist_ok=True)
            file_path = csv_dir / f'followed_users_batch_{timestamp}.csv'
            
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                writer.writerow(['Username', 'Followed At', 'Batch Size'])  # Header
                    for username in usernames:
                    writer.writerow([username, datetime.now().isoformat(), len(usernames)])
                
            self.log(f"💾 Auto-exported {len(usernames)} accounts to: {file_path.name}", 'follow')
                
        except Exception as e:
            self.log(f"❌ Error auto-exporting CSV: {str(e)}", 'follow')

class BotWorker(QThread):
    log_signal = pyqtSignal(str)
    finished = pyqtSignal(list)
    
    def __init__(self, bot, action_type):
        super().__init__()
        self.bot = bot
        self.action_type = action_type
        self.processed_accounts = []

    def run(self):
        try:
            if self.action_type == 'follow':
                self.processed_accounts = self.bot.run(self.log_signal)
            else:  # unfollow
                self.processed_accounts = self.bot.run_unfollow(self.log_signal)
        except Exception as e:
            self.log_signal.emit(f"Error: {str(e)}")
        finally:
            self.finished.emit(self.processed_accounts)

def main():
    app = QApplication(sys.argv)
    gui = InstagramAutomationGUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 