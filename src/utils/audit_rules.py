import yaml
from typing import Dict, List, Optional
from pathlib import Path
import os

class AuditRule:
    def __init__(self, name: str, command: str, pattern: str, severity: str, description: str):
        self.name = name
        self.command = command
        self.pattern = pattern
        self.severity = severity
        self.description = description

class AuditRuleManager:
    def __init__(self):
        # Get the project root directory (where main.py is located)
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / 'audit_rules'
        
        # Create directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)
        
        # If no rules exist, create default rules
        if not list(self.config_dir.glob('*.yaml')):
            self._create_default_rules()
            
        self.rules: Dict[str, AuditRule] = {}
        self.load_rules()

    def _create_default_rules(self):
        """Create default rules file if none exist"""
        default_rules = {
            'rules': [
                {
                    'name': "Weak Password Policy",
                    'command': "show running-config | include password",
                    'pattern': "password.*0",
                    'severity': "High",
                    'description': "Weak password encryption detected"
                },
                {
                    'name': "Telnet Enabled",
                    'command': "show running-config | include line vty",
                    'pattern': "transport input telnet",
                    'severity': "Critical",
                    'description': "Telnet access is enabled"
                },
                {
                    'name': "SNMP Public Community",
                    'command': "show running-config | include snmp-server community",
                    'pattern': "public",
                    'severity': "High",
                    'description': "SNMP using public community string"
                }
            ]
        }
        
        with open(self.config_dir / 'default_rules.yaml', 'w') as f:
            yaml.dump(default_rules, f, default_flow_style=False)

    def load_rules(self):
        """Load all audit rules from YAML files"""
        self.rules.clear()
        for file in self.config_dir.glob('*.yaml'):
            try:
                with open(file, 'r') as f:
                    data = yaml.safe_load(f)
                    if data and 'rules' in data:
                        for rule_data in data['rules']:
                            rule = AuditRule(
                                name=rule_data['name'],
                                command=rule_data['command'],
                                pattern=rule_data['pattern'],
                                severity=rule_data['severity'],
                                description=rule_data['description']
                            )
                            self.rules[rule.name] = rule
            except Exception as e:
                print(f"Error loading rules from {file}: {e}")

    def save_rule(self, rule: AuditRule, filename: str = 'custom_rules.yaml'):
        """Save a new audit rule"""
        filepath = self.config_dir / filename
        
        # Load existing rules or create new file
        if filepath.exists():
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f) or {'rules': []}
        else:
            data = {'rules': []}

        # Add new rule
        rule_data = {
            'name': rule.name,
            'command': rule.command,
            'pattern': rule.pattern,
            'severity': rule.severity,
            'description': rule.description
        }
        
        # Update if exists, append if new
        for existing_rule in data['rules']:
            if existing_rule['name'] == rule.name:
                existing_rule.update(rule_data)
                break
        else:
            data['rules'].append(rule_data)

        # Save to file
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
        
        # Reload rules
        self.load_rules()

    def delete_rule(self, rule_name: str):
        """Delete an audit rule"""
        for file in self.config_dir.glob('*.yaml'):
            with open(file, 'r') as f:
                data = yaml.safe_load(f)
            
            # Remove rule if found
            data['rules'] = [r for r in data['rules'] if r['name'] != rule_name]
            
            # Save file if modified
            with open(file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
        
        # Reload rules
        self.load_rules()

    def get_rule(self, name: str) -> Optional[AuditRule]:
        """Get a specific rule by name"""
        return self.rules.get(name)

    def get_all_rules(self) -> List[AuditRule]:
        """Get all available rules"""
        return list(self.rules.values()) 