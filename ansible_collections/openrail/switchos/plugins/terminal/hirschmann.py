from ansible.plugins.terminal import TerminalBase
from ansible.errors import AnsibleConnectionFailure

import re

class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(br"\(BXP\)>"),
    ]

    terminal_stderr_re = [
        re.compile(br"Error: Invalid command"),
    ]

    def on_open_shell(self):
        try:
            self._exec_cli_command(b'cli numlines 0')
        except AnsibleConnectionFailure as exc:
            raise AnsibleConnectionFailure('unable to set terminal parameters') from exc

    def on_become(self):
        if self._get_prompt().endswith(b'#'):
            return
        
        try:
            self._exec_cli_command(b'enable')
        except AnsibleConnectionFailure as exc:
            raise AnsibleConnectionFailure('unable to become') from exc
        
    def on_unbecome(self):
        prompt = self._get_prompt()
        if prompt is None:
            # if prompt is None most likely the terminal is hung up at a prompt
            return

        if prompt.strip().endswith(b'(Config)#'):
            self._exec_cli_command(b'exit')

        if prompt.endswith(b'(BXP)#'):
            self._exec_cli_command(b'disable')
        else:
            raise AnsibleConnectionFailure(f'Unexpected prompt: {prompt}')