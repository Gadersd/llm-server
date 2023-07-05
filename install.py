from xml.sax import _create_parser
import paramiko
from paramiko.ssh_exception import NoValidConnectionsError
from scp import SCPClient
import os
import shutil
import glob
import subprocess
import sys
import tempfile
import platform

# Set pem file's permissions to ~600
def set_permissions(file):
    if platform.system() == 'Windows':
        import win32security
        import ntsecuritycon as con
        import getpass

        username = getpass.getuser()

        user_sid, domain, type = win32security.LookupAccountName("", username)

        sd = win32security.GetFileSecurity(file, win32security.DACL_SECURITY_INFORMATION)
        dacl = win32security.ACL()
        
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_GENERIC_READ | con.FILE_GENERIC_WRITE, user_sid)
        
        sd.SetSecurityDescriptorDacl(1, dacl, 0)   # may not be necessary
        win32security.SetFileSecurity(file, win32security.DACL_SECURITY_INFORMATION, sd)
    else:
        os.chmod(file, 0o600)

def run_commands_in_new_terminal(commands: list):
    concatenated_commands = " && ".join(commands)
    if sys.platform == "win32":
        subprocess.Popen('start cmd.exe /k ' + concatenated_commands, shell=True)
    elif sys.platform == "darwin":
        script = 'tell application "Terminal" to do script "' + concatenated_commands + '"'
        subprocess.Popen(["osascript", "-e", script])
    elif "linux" in sys.platform:
        subprocess.Popen(['open', '-a', 'Terminal', 'bash', '-c', concatenated_commands])
    else:
        raise NotImplementedError(sys.platform)

def make_archive(source, destination):
    base = os.path.basename(destination)
    name = base.split('.')[0]
    format = base.split('.')[1]
    
    # create a temporary directory
    dirpath = tempfile.mkdtemp()

    # copytree function with ignore .pem files
    shutil.copytree(source, dirpath+'/llm', ignore=shutil.ignore_patterns('*.pem'))

    shutil.make_archive(name, format, dirpath, 'llm')
    shutil.move('%s.%s' % (name, format), destination)
    
    # remove the temporary directory
    shutil.rmtree(dirpath)

# Ask the user for the IP address
IP = input("Enter the IP address: ")

# Look for the .pem file in the current directory
pem_files = glob.glob('*.pem')
if not pem_files:
    print("No .pem file found in the current directory! Please place the .pem file in the current directory.")
    exit(1)

ssh_key_file_path = pem_files[0]  # Use the first .pem file found 
ssh_key_file_path_global = os.path.abspath(pem_files[0])

# Create a SSH client
ssh = paramiko.SSHClient()
ssh.load_system_host_keys()
#ssh.set_missing_host_key_policy(paramiko.WarningPolicy)
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Set pem file's permissions to 600 for ssh to work
set_permissions(ssh_key_file_path)

# Zip the current directory
print("Zipping current directory...")
current_directory_name = os.path.basename(os.getcwd())
zip_file_name = f'{current_directory_name}.zip'
make_archive('.', zip_file_name)

# Connect to the server
print("Connecting to the server...")

try:
    ssh.connect(hostname=IP, username='ubuntu', key_filename=ssh_key_file_path)
except NoValidConnectionsError:
    print('SSH connection failed. Check your internet connection or server status.')
    exit(1)

# Transfer the zipped file to the remote server
print("Transferring zipped file to the remote server...")
scp = SCPClient(ssh.get_transport())
scp.put(zip_file_name, f"~/"+zip_file_name)

# Unzip the file on the server
print("Unzip the file on the server...")
stdin, stdout, stderr = ssh.exec_command('unzip -o ~/'+zip_file_name)
#print(stdout.read().decode(), stderr.read().decode())

# Delete the zip
print("Deleting the zip...")
os.remove(zip_file_name)

# Ensures scripts are executable
stdin, stdout, stderr = ssh.exec_command('find ./llm/server -name "*.sh" -exec chmod +x {} \\;')
#print(stdout.read().decode(), stderr.read().decode())

# Run setup on remote server
print("Running setup on the remote server...")
stdin, stdout, stderr = ssh.exec_command(f'./llm/server/setup.sh')
print(stdout.read().decode(), stderr.read().decode())

# Generate certificate and key 
print("Generating certificate and key...")
stdin, stdout, stderr = ssh.exec_command(f'./llm/server/generate_certificate.sh {IP}')
print(stdout.read().decode(), stderr.read().decode())

# Retrieve cert_and_key.p12 from server
print("Retrieving my-ca.crt from server...")
os.makedirs('./cert', exist_ok=True)
scp.get(f'~/llm/server/cert/my-ca.crt', './cert/my-ca.crt')

# Set secure file permissions to read and write for the owner only
set_permissions('./cert/my-ca.crt')

# Close the SSH connection
print("Closing the SSH connection...")
ssh.close()

commands = [f'ssh -i {ssh_key_file_path_global} ubuntu@{IP}']
print('Now run "python3 test.py" and if successful then "python3 chat_server_global.py". Both scripts are in llm/server')
run_commands_in_new_terminal(commands)

print("Operation completed successfully.")
