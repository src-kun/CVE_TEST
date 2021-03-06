# Main program ource
# Vagrantfile creation using a generic template
# Shell provisioning method used
# Pass absolute file name of exploit program to be run as initial argument
# Asks for box to be installed, Shared directory location and list of packages to be installed on VM
# Copies exploit program into /vagrant_data directory on VM

#!/usr/bin/python

import sys
import os
import shutil
import subprocess
from subprocess import call

def vm_creation():

	boxname = raw_input('Please enter the name of box : ')
	box_url = raw_input('Please enter the url of box you want : ')
	syncfolder = raw_input('Please enter absolute host shared folder name : ')
	memory = raw_input('Please enter the memory required : ')
	shared_dir = '/vagrant_data'  #guest local shared dir

	# Copying exploit program
	print('Copying exploit program in local directory')
	for line in exploit_file:
		line=line.replace("\n","")
		shutil.copy2(line,syncfolder+'/'+line.split()[-1])
		os.chmod(syncfolder+'/'+line.split()[-1],0755)

	call(["rm","-f","Vagrantfile"])
	print('Initializing Vagrant\n')
	#Modifying Vagrantfile starts
	vagrant_template = open(syncfolder+'/Vagrantfile','r') #common template
	vagrant_file = open(os.getcwd()+'/Vagrantfile','w') #final actual file

	replacements = {'BOX_NAME':boxname , 'HOST_SHARED_DIR':syncfolder , 'GUEST_MOUNT_DIR':shared_dir , 'MEMORY':memory , 'BOX_URL':box_url}

	for line in vagrant_template:
		for src,dest in replacements.iteritems():
			line = line.replace(src , dest)
		vagrant_file.write(line)

	vagrant_template.close()
	vagrant_file.close()
	#Modifying Vagrantfile ends  

	#puppet modules to be installed
	#ensure that puppet is installed on Host
	puppet_mod_install = open ('puppet.sh','w')

	new_kernel=raw_input('Do you want to install new kernel(vagrant may have problems later) [y/n]: ')
	if new_kernel == '' or new_kernel == 'n':
		kernel_deb_dir=''
		print('Default is no\n')

	if new_kernel == 'y':
		kernel_deb_dir=raw_input('enter the location of new kernel source(deb files) you want to build: ')
		kernel_version=raw_input('enter the kernel version : ')

	if kernel_deb_dir != '':
		puppet_mod_install.write('cp ' + kernel_deb_dir + '/*.deb ' + syncfolder +'\n')

	num = raw_input('How many puppet modules you want to install : ')
	if not num.isdigit():
		print('Defaulting to zero ')
		num=0
	for i in range(int(num)):
		j=0
		x=raw_input('Enter the module-name and version if any : ')
		for val in x.split():
			if j==1:
				version = val
			if j==0:
				module_name = val
				version = ''
				j=j+1
		if version != '':
			puppet_mod_install.write('puppet module list --modulepath ' + os.getcwd() + '/puppet/modules | grep -w '+ module_name + ' || ' +'puppet module install --modulepath ' + os.getcwd() + '/puppet/modules ' + module_name + ' --version ' + '\"<=' + version + '\"' +'\n' )
		else:
			puppet_mod_install.write('puppet module list --modulepath ' + os.getcwd() + '/puppet/modules | grep -w '+ module_name + ' || ' + 'puppet module install --modulepath ' + os.getcwd() + '/puppet/modules ' + module_name +'\n' )

	#puppet_list = raw_input('Please enter the puppet modules you want in order\n')
	#for module in puppet_list.split():
	#        puppet_mod_install.write('puppet module install --force --modulepath ' + os.getcwd() + '/puppet/modules ' + module + '\n' )
	puppet_mod_install.close()
	#Download puppet modules
	os.chmod("./puppet.sh",0755)
	call("./puppet.sh",shell=True)

	#Creating shell provisioning file
	prov_file = open(os.getcwd()+'/provision.sh','w')
	prov_file.write('#!/usr/bin/env bash\n')
	prov_file.write('#update the server\n')
	prov_file.write('sudo apt-get update \n')
	#prov_file.write('sudo apt-get -y upgrade \n')
	prov_file.write('sudo apt-get -y install dkms build-essential linux-headers-generic vim gcc puppet*\n')

	package_list=raw_input('Please enter list of sudo packages you want in VM : ')
	for package in package_list.split():
		prov_file.write('sudo apt-get install -y ' + package + '\n')

	#Coying all files from shared directory.Kernel rebuild destroys shared directory
	prov_file.write('sudo mkdir /temp\n')
	prov_file.write('sudo cp ' + shared_dir +'/* /temp \n' )
	if kernel_deb_dir != '':
		prov_file.write('sudo apt-get install linux-headers-'+kernel_version+'*\n')
		prov_file.write('sudo dpkg -i /temp/*.deb\n')

	prov_file.close();

#Main flow of script
if len(sys.argv)!=2:
	print 'please enter absolute exploit list file name'
	print 'usage : python main.py <filename> \nExiting'
	sys.exit(1)

print 'Arguments are :'
for list in sys.argv:
	print list

exploit_file = open(sys.argv[1],'r')
program_list = []  #List of exploit binaries name to be run
for line in exploit_file:
	line=line.replace("\n","")
	program_list.append(line.split("/")[-1])

new_vm=raw_input('Do you want to create new VM from scratch [y/n]: ')
if new_vm == 'y':
	vm_creation()

print 'Please ensure default.pp is correct'
proceed=raw_input('Do you want to proceed with VM setup and exploit run [y/n] : ')
if proceed == 'y':
	call(["vagrant","up"])
	#Running exploits in the VM - considering the compiled code is "exploit"
	exploit_run=raw_input('Do you want to run exploits in VM [y/n] : ')
	if exploit_run=='y':
		for binary in program_list: 
	                #call("./puppet.sh",shell=True)
			vm_user=subprocess.Popen(["vagrant","ssh","-c","whoami"],stdout=subprocess.PIPE).communicate()[0].strip()
			print'Presently VM user is : ',vm_user
			print 'Executing binary : ',binary
			args=raw_input('Enter arguments for above exploit if any : ')
			return_code=call(["vagrant","ssh", "-c","/vagrant_data/"+binary+" "+args])
			print 'return code is ',return_code
			if return_code != 0:
				print 'exploit execution failed..!Check again'
			vm_user=subprocess.Popen(["vagrant","ssh","-c","whoami"],stdout=subprocess.PIPE).communicate()[0].strip()
			#print'After execution VM user is : ',vm_user
