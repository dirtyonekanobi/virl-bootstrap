#!/usr/bin/python
#__author__ = 'ejk'


"""virl install.

Usage:
  foo.py zero | first | second | third | fourth | salt | test | iso | wrap | desktop | rehost | renumber | compute | all | images | password

Options:
  --version             shows program's version number and exit
  -h, --help            show this help message and exit
"""

#from configparser import ConfigParser
import configparser
import subprocess
import logging
import envoy
from time import sleep
from tempfile import mkstemp
from shutil import move, copy, copystat, rmtree
#from os import remove, close, unsetenv, chdir, mkdir, system, path
from os import remove, close, mkdir, system, path, makedirs
from docopt import docopt


#TODO old pos logging style for now
#Setting up logging
log = logging.getLogger('install')
log.setLevel(logging.DEBUG)
fhand = logging.FileHandler('/tmp/install.out')
fhand.setLevel(logging.WARNING)
# console messages
conhand = logging.StreamHandler()
conhand.setLevel(logging.ERROR)
# formatter
frmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fhand.setFormatter(frmt)
conhand.setFormatter(frmt)
log.addHandler(fhand)
log.addHandler(conhand)


safeparser = configparser.ConfigParser()
safeparser_file = '/etc/virl.ini'
# safeparser_backup_file = '/home/virl/vsettings.ini'
if path.exists(safeparser_file):
    safeparser.read('/etc/virl.ini')
# elif path.exists(safeparser_backup_file):
#     safeparser.read('/home/virl/vsettings.ini')
else:
    print "No config exists at /etc/virl.ini.  Exiting"
    exit(1)
    # safeparser.read('./settings.ini')
DEFAULT = safeparser['DEFAULT']
# install = safeparser['install']
# operational = safeparser['operational']
# packaging = safeparser['packaging']
# testing = safeparser['testing']
# cluster = safeparser['cluster']


hostname = safeparser.get('DEFAULT', 'hostname', fallback='virl')
fqdn = safeparser.get('DEFAULT', 'domain', fallback='cisco.com')

dhcp_public = safeparser.getboolean('DEFAULT', 'using_dhcp_on_the_public_port', fallback=True)
public_port = safeparser.get('DEFAULT', 'public_port', fallback='eth0')
public_ip = safeparser.get('DEFAULT', 'Static_IP', fallback='127.0.0.1')
public_network = safeparser.get('DEFAULT', 'public_network', fallback='172.16.6.0')
public_netmask = safeparser.get('DEFAULT', 'public_netmask', fallback='255.255.255.0')
public_gateway = safeparser.get('DEFAULT', 'public_gateway', fallback='172.16.6.1')
proxy = safeparser.getboolean('DEFAULT', 'proxy', fallback=False)
http_proxy = safeparser.get('DEFAULT', 'http_proxy', fallback='http://proxy-wsa.esl.cisco.com:80/')
ntp_server = safeparser.get('DEFAULT', 'ntp_server', fallback='ntp.ubuntu.com')
dns1 = safeparser.get('DEFAULT', 'first_nameserver', fallback='8.8.8.8')
dns2 = safeparser.get('DEFAULT', 'second_nameserver', fallback='171.70.168.183')


l2_port = safeparser.get('DEFAULT', 'l2_port', fallback='eth1')
l2_mask = safeparser.get('DEFAULT', 'l2_mask', fallback='255.255.255.0')
l2_bridge_port = safeparser.get('DEFAULT', 'l2_bridge_port', fallback='br-eth1')
l2_address = safeparser.get('DEFAULT', 'l2_address', fallback='172.16.1.254')
l2_network = safeparser.get('DEFAULT', 'l2_network', fallback='172.16.1.0/24')
l2_gate = safeparser.get('DEFAULT', 'l2_network_gateway', fallback='172.16.1.1')
l2_s_address = safeparser.get('DEFAULT', 'l2_start_address', fallback='172.16.1.50')
l2_e_address = safeparser.get('DEFAULT', 'l2_end_address', fallback='172.16.1.250')
# address_l2_port = safeparser.getboolean('DEFAULT', 'address l2 port', fallback=True)
address_l2_port = True
flat_dns1 = safeparser.get('DEFAULT', 'first_flat_nameserver', fallback='8.8.8.8')
flat_dns2 = safeparser.get('DEFAULT', 'second_flat_nameserver', fallback='8.8.4.4')

l2_port2_enabled = safeparser.getboolean('DEFAULT', 'l2_port2_enabled', fallback=True)
l2_port2 = safeparser.get('DEFAULT', 'l2_port2', fallback='eth2')
l2_mask2 = safeparser.get('DEFAULT', 'l2_mask2', fallback='255.255.255.0')
l2_bridge_port2 = safeparser.get('DEFAULT', 'l2_bridge_port2', fallback='br-eth2')
l2_address2 = safeparser.get('DEFAULT', 'l2_address2', fallback='172.16.2.254')
l2_network2 = safeparser.get('DEFAULT', 'l2_network2', fallback='172.16.2.0/24')
l2_gate2 = safeparser.get('DEFAULT', 'l2_network_gateway2', fallback='172.16.2.1')
l2_s_address2 = safeparser.get('DEFAULT', 'l2_start_address2', fallback='172.16.2.50')
l2_e_address2 = safeparser.get('DEFAULT', 'l2_end_address2', fallback='172.16.2.250')
# address_l2_port2 = safeparser.getboolean('DEFAULT', 'address l2 port2', fallback=True)
address_l2_port2 = True
flat2_dns1 = safeparser.get('DEFAULT', 'first_flat2_nameserver', fallback='8.8.8.8')
flat2_dns2 = safeparser.get('DEFAULT', 'second_flat2_nameserver', fallback='8.8.4.4')


RAMDISK = safeparser.getboolean('DEFAULT', 'ramdisk', fallback=False)
ank = safeparser.get('DEFAULT', 'ank', fallback='19401')
uwm_port = safeparser.get('DEFAULT', 'virl_user_management', fallback='19400')
wsgi_port = safeparser.get('DEFAULT', 'virl_webservices', fallback='19399')
serial_start = safeparser.get('DEFAULT', 'Start_of_serial_port_range', fallback='17000')
serial_end = safeparser.get('DEFAULT', 'End_of_serial_port_range', fallback='18000')

guest_account = safeparser.getboolean('DEFAULT', 'guest_account', fallback=True)
user_list = safeparser.get('DEFAULT', 'user_list', fallback='')
user_list_limited = safeparser.get('DEFAULT', 'restricted_users', fallback='')

l3_port = safeparser.get('DEFAULT', 'l3_port', fallback='eth3')
l3_mask = safeparser.get('DEFAULT', 'l3_mask', fallback='255.255.255.0')
l3_bridge_port = safeparser.get('DEFAULT', 'l3_bridge_port', fallback='br-ex')
l3_s_address = safeparser.get('DEFAULT', 'l3_floating_start_address', fallback='172.16.3.50')
l3_e_address = safeparser.get('DEFAULT', 'l3_floating_end_address', fallback='172.16.3.250')
l3_address = safeparser.get('DEFAULT', 'l3_address', fallback='172.16.3.254')
l3_gate = safeparser.get('DEFAULT', 'l3_network_gateway', fallback='172.16.3.1')
l3_network = safeparser.get('DEFAULT', 'l3_network', fallback='172.16.3.0/24')
snat_dns1 = safeparser.get('DEFAULT', 'first_snat_nameserver', fallback='8.8.8.8')
snat_dns2 = safeparser.get('DEFAULT', 'second_snat_nameserver', fallback='8.8.4.4')
location_region = safeparser.get('DEFAULT', 'location_region', fallback='US')
vnc = safeparser.getboolean('DEFAULT', 'vnc', fallback=False)
vnc_passwd = safeparser.get('DEFAULT', 'vnc_password', fallback='letmein')

#Install section
uwm_username = safeparser.get('DEFAULT', 'uwm_username', fallback='uwmadmin')
uwmadmin_passwd = safeparser.get('DEFAULT', 'uwmadmin_password', fallback='password')
guest_passwd = safeparser.get('DEFAULT', 'guest_password', fallback='guest')
ospassword = safeparser.get('DEFAULT', 'password', fallback='password')
mypassword = safeparser.get('DEFAULT', 'mysql_password', fallback='password')
ks_token = safeparser.get('DEFAULT', 'keystone_service_token', fallback='fkgjhsdflkjh')

ganglia = safeparser.getboolean('DEFAULT', 'ganglia', fallback=False)

debug = safeparser.getboolean('DEFAULT', 'debug', fallback=False)
horizon = safeparser.getboolean('DEFAULT', 'enable_horizon', fallback=False)
ceilometer = safeparser.getboolean('DEFAULT', 'ceilometer', fallback=False)
heat = safeparser.getboolean('DEFAULT', 'enable_heat', fallback=True)
cinder = safeparser.getboolean('DEFAULT', 'enable_cinder', fallback=False)
cinder_file = safeparser.getboolean('DEFAULT', 'cinder_file', fallback=True)
cinder_device = safeparser.get('DEFAULT', 'cinder_device', fallback=False )
cinder_size = safeparser.get('DEFAULT', 'cinder_size', fallback=2000 )
cinder_loc = safeparser.get('DEFAULT', 'cinder_location', fallback='/var/lib/cinder/cinder-volumes.lvm')
neutron_switch = safeparser.get('DEFAULT', 'neutron_switch', fallback='linuxbridge')
desktop = safeparser.getboolean('DEFAULT', 'desktop', fallback=False)

#Packaging section
cariden = safeparser.getboolean('DEFAULT', 'cariden', fallback=False)
NNI = safeparser.getboolean('DEFAULT', 'NNI', fallback=False)
GITBRANCH = safeparser.get('DEFAULT', 'GIT_branch', fallback='grizzly')
NOVABRANCH = safeparser.get('DEFAULT', 'Nova_branch', fallback='grizzly-virl-telnet')
BASEDIR = safeparser.get('DEFAULT', 'virl.standalone_is_in_what_directory', fallback='/home/virl/virl.standalone/')
GITBASE = safeparser.get('DEFAULT', 'base_of_the_git_tree_is_in_what_directory',
                         fallback='/home/virl/virl.standalone/glocal')
multiuser = safeparser.getboolean('DEFAULTl', 'multiuser', fallback=True)
install1q = safeparser.getboolean('DEFAULT', 'Install_1q', fallback=True)
packer_calls = safeparser.getboolean('DEFAULT', 'packer', fallback=False)
vagrant_calls = safeparser.getboolean('DEFAULT', 'vagrant', fallback=False)
vagrant_pre_fourth = safeparser.getboolean('DEFAULT', 'vagrant_before_fourth', fallback=False)
vagrant_keys = safeparser.getboolean('DEFAULT', 'vagrant_keys', fallback=False)
cml = safeparser.getboolean('DEFAULT', 'cml', fallback=False)


#Operational Section
image_set = safeparser.get('DEFAULT', 'image_set', fallback='internal')
salt = safeparser.getboolean('DEFAULT', 'salt', fallback=True)
salt_master = safeparser.get('DEFAULT', 'salt_master', fallback='none')
salt_id = safeparser.get('DEFAULT', 'salt_id', fallback='virl')
salt_domain = safeparser.get('DEFAULT', 'salt_domain', fallback='virl.info')
virl_type = safeparser.get('DEFAULT', 'Is_this_a_stable_or_testing_server', fallback='stable')
cisco_internal = safeparser.getboolean('DEFAULT', 'inside_cisco', fallback=False)
onedev = safeparser.getboolean('DEFAULT', 'onedev', fallback=False)

dummy_int = safeparser.getboolean('DEFAULT', 'dummy_int', fallback=False)
jumbo_frames = safeparser.getboolean('DEFAULT', 'jumbo_frames', fallback=False)

#Testing Section
icehouse = safeparser.getboolean('DEFAULT', 'icehouse', fallback=True)
testingank = safeparser.getboolean('DEFAULT', 'testing_ank', fallback=False)
testingstd = safeparser.getboolean('DEFAULT', 'testing_std', fallback=False)
testingvmm = safeparser.getboolean('DEFAULT', 'testing_vmm', fallback=False)
#ankstable = safeparser.getboolean('DEFAULT', 'stable ank', fallback=False)
v144 = safeparser.getboolean('DEFAULT', 'v144', fallback=True)

#devops section
testingdevops = safeparser.getboolean('DEFAULT', 'testing_devops', fallback=False)

#cluster section
controller = safeparser.getboolean('DEFAULT', 'this node is the controller', fallback=True)
internalnet_controller_ip = safeparser.get('DEFAULT', 'internalnet_controller_IP', fallback='172.16.10.250')
internalnet_controller_hostname = safeparser.get('DEFAULT', 'internalnet_controller_hostname', fallback='controller')
internalnet_port = safeparser.get('DEFAULT', 'internalnet_port', fallback='eth4')
internalnet_ip = safeparser.get('DEFAULT', 'internalnet_IP', fallback='172.16.10.250')
internalnet_network = safeparser.get('DEFAULT', 'internalnet_network', fallback='172.16.10.0')
internalnet_netmask = safeparser.get('DEFAULT', 'internalnet_netmask', fallback='255.255.255.0')
internalnet_gateway = safeparser.get('DEFAULT', 'internalnet_gateway', fallback='172.16.10.1')



if dhcp_public or packer_calls:
    public_ip = '127.0.1.1'

if cisco_internal and cml:
    std_loc = 'http://wwwin-drrc.cisco.com/virl/std/cml/stable/'
    ank_loc = 'http://wwwin-drrc.cisco.com/ank/release/stable/'
elif cisco_internal and not cml:
    std_loc = 'http://wwwin-drrc.cisco.com/virl/std/release/stable/'
    ank_loc = 'http://wwwin-drrc.cisco.com/ank/release/stable/'
else:
    std_loc = 'bins/std'
    ank_loc = 'bins/ank/'


qadmincall = ['/usr/bin/neutron', '--os-tenant-name', 'admin', '--os-username', 'admin', '--os-password',
              '{0}'.format(ospassword), '--os-auth-url=http://localhost:5000/v2.0']
nadmincall = ['/usr/bin/nova', '--os-tenant-name', 'admin', '--os-username', 'admin', '--os-password',
              '{0}'.format(ospassword), '--os-auth-url=http://localhost:5000/v2.0']
kcall = ['/usr/bin/keystone', '--os-tenant-name', 'admin', '--os-username', 'admin', '--os-password',
         '{0}'.format(ospassword), '--os-auth-url=http://localhost:5000/v2.0']
cpstr = 'sudo -S cp -f "%(from)s" "%(to)s"'
lnstr = 'sudo -S ln -sf "%(orig)s" "%(link)s"'


def replace(file_path, pattern, subst):
    #Create temp file
    fh, abs_path = mkstemp()
    new_file = open(abs_path, 'w')
    old_file = open(file_path)
    for line in old_file:
        new_file.write(line.replace(pattern, subst))
        #close temp file
    new_file.close()
    close(fh)
    old_file.close()
    #Save permission state
    copystat(file_path, abs_path)
    #Remove original file
    remove(file_path)
    #Move new file
    move(abs_path, file_path)


def setup_salt():
    if not path.exists('/usr/bin/salt-minion'):
        subprocess.call(['sudo', '-s', (BASEDIR + 'install_scripts/setup_salt')])
    if not salt_master == 'none':
        subprocess.call(['sudo', 'sed', '-i', 's/#master: salt/master: {master}/g'.format(master=salt_master),
                         '/etc/salt/minion'])

def alter_virlcfg():

    if not uwm_port == '19399':
        subprocess.call(['sudo', '/usr/local/bin/virl_config', 'update', '--global', '--uwm-port', uwm_port])
    if not wsgi_port == '19400':
        subprocess.call(['sudo', '/usr/local/bin/virl_config', 'update', '--global', '--std-port', wsgi_port])
        subprocess.call(['sudo', 'sed', '-i', ('s/:19399/:{0}/g'.format(uwm_port)),
                         ('/var/www/html/index.html')])
    if not dhcp_public:
        subprocess.call(['sudo', '/usr/local/bin/virl_config', 'update', '--global', '--openstack-auth-url',
                         'http://{0}:5000/v2.0'.format(public_ip)])
    if not ospassword == 'password':
        subprocess.call(['sudo', '/usr/local/bin/virl_config', 'update', '--global',
                         '--openstack-password', ospassword])
    subprocess.call(['sudo', 'crudini', '--set','/etc/virl/virl.cfg', 'env',
                         'virl_openstack_password', (' ' + ospassword)])
    subprocess.call(['sudo', 'crudini', '--set','/etc/virl/virl.cfg', 'env',
                         'virl_openstack_service_token', (' ' + ks_token)])
    subprocess.call(['sudo', 'crudini', '--set','/etc/virl/virl.cfg', 'env',
                         'virl_std_port', (' ' + wsgi_port)])
    subprocess.call(['sudo', 'crudini', '--set','/etc/virl/virl.cfg', 'env',
                         'virl_std_url', (' ' + 'http://localhost:{0}'.format(wsgi_port))])
    subprocess.call(['sudo', 'crudini', '--set','/etc/virl/virl.cfg', 'env',
                         'virl_uwm_url', (' ' + 'http://localhost:{0}'.format(uwm_port))])
    subprocess.call(['sudo', 'crudini', '--set','/etc/virl/virl.cfg', 'env',
                         'virl_uwm_port', (' ' + uwm_port)])
    subprocess.call(['sudo', 'crudini', '--set','/usr/local/lib/python2.7/dist-packages/virl_pkg_data/conf/builtin.cfg',
                     'orchestration', 'network_security_groups', ' False'])


def building_salt_extra():
    if not path.exists('/etc/salt/virl'):
        subprocess.call(['sudo', 'mkdir', '-p', '/etc/salt/virl'])
    if path.exists('/usr/local/bin/keystone') or path.exists('/usr/bin/keystone'):
        admin_tenid = (subprocess.check_output(['keystone --os-tenant-name admin --os-username admin'
                                            ' --os-password {ospassword} --os-auth-url=http://localhost:5000/v2.0'
                                            ' tenant-list | grep -w "admin" | cut -d "|" -f2'
                                           .format(ospassword=ospassword)], shell=True)[1:33])
        neutron_extnet_id = (subprocess.check_output(['neutron --os-tenant-name admin --os-username admin'
                                            ' --os-password {ospassword} --os-auth-url=http://localhost:5000/v2.0'
                                            ' net-list | grep -w "ext-net" | cut -d "|" -f2'
                                           .format(ospassword=ospassword)], shell=True)[1:33])
    else:
        admin_tenid = ''
        neutron_extnet_id = ''
    with open(("/tmp/extra"), "w") as extra:
        if not salt_master == 'none' or vagrant_pre_fourth:
            extra.write("""master: \n""")
            for each in salt_master.split(','):
                extra.write("""  - {each}\n""".format(each=each))
            extra.write("""master_shuffle: True \n""")
            extra.write("""master_alive_interval: 180 \n""")
        else:
            extra.write("""file_client: local\n""")
        extra.write("""id: {salt_id}\n""".format(salt_id=salt_id))
        extra.write("""append_domain: {salt_domain}\n""".format(salt_domain=salt_domain))
        extra.write("""grains_dirs:\n""")
        extra.write("""  - /etc/salt/virl\n""")

    with open(("/tmp/grains"), "w") as grains:
        # for section_name in safeparser.sections():
        if cinder_device or cinder_file:
            grains.write("""  cinder_enabled: True\n""")
        else:
            grains.write("""  cinder_enabled: False\n""")
        if not uwm_port == '14000':
            grains.write("""  uwm_url: http://{0}:{1}\n""".format(public_ip,uwm_port))
        for name, value in safeparser.items('DEFAULT'):
            grains.write("""  {name}: {value}\n""".format(name=name, value=value))
        grains.write("""  neutron_extnet_id: {neutid}\n""".format(neutid=neutron_extnet_id))
    with open(("/tmp/openstack"), "w") as openstack:
        openstack.write("""keystone.user: admin
keystone.password: {ospassword}
keystone.tenant: admin
keystone.tenant_id: {tenid}
keystone.auth_url: 'http://127.0.0.1:5000/v2.0/'
keystone.token: {kstoken}
mysql.user: root
mysql.pass: {mypass}\n""".format(ospassword=ospassword, kstoken=ks_token, tenid=admin_tenid, mypass=mypassword))
    subprocess.call(['sudo', 'cp', '-f', ('/tmp/extra'), '/etc/salt/minion.d/extra.conf'])
    subprocess.call(['sudo', 'cp', '-f', ('/tmp/openstack'),
                             '/etc/salt/minion.d/openstack.conf'])
    subprocess.call(['sudo', 'cp', '-f', ('/tmp/grains'), '/etc/salt'])
    subprocess.call(['sudo', 'service', 'salt-minion', 'restart'])


def create_basic_networks():
    user = 'admin'
    password = ospassword
    qcall = ['/usr/bin/neutron', '--os-tenant-name', '{0}'.format(user), '--os-username', '{0}'.format(user),
             '--os-password', '{0}'.format(password), '--os-auth-url=http://localhost:5000/v2.0']
    subprocess.call(qcall + ['quota-update', '--router', '-1'])
    try:
        if not varg['iso']:
            # system(cpstr % {'from': (BASEDIR + 'install_scripts/init.d/virl-uwm.init'), 'to': '/etc/init.d/virl-uwm'})
            # system(lnstr % {'orig': '/etc/init.d/virl-uwm', 'link': '/etc/rc2.d/S98virl-uwm'})

            if 'ext-net' not in subprocess.check_output(qcall + ['net-list']):
                subprocess.call(qcall + ['net-create', 'ext-net', '--shared', '--provider:network_type', 'flat',
                                         '--router:external', 'true', '--provider:physical_network', 'ext-net'])
            if 'flat' not in subprocess.check_output(qcall + ['net-list']):
                subprocess.call(qcall + ['net-create', 'flat', '--shared', '--provider:network_type', 'flat',
                                         '--provider:physical_network', 'flat'])
            if 'flat1' not in subprocess.check_output(qcall + ['net-list']) and l2_port2_enabled:
                subprocess.call(qcall + ['net-create', 'flat1', '--shared', '--provider:network_type', 'flat',
                                         '--provider:physical_network', 'flat1'])

        if 'ext-net' not in subprocess.check_output(qcall + ['subnet-list']):
            subprocess.call(qcall + ['subnet-create', 'ext-net', '{0}'.format(l3_network), '--allocation-pool',
                            'start={0},end={1}'.format(l3_s_address, l3_e_address), '--gateway',
                            '{0}'.format(l3_gate), '--name', 'ext-net', '--dns-nameservers', 'list=true',
                            '{0}'.format(snat_dns2), '{0}'.format(snat_dns1)])
        if 'flat' not in subprocess.check_output(qcall + ['subnet-list']):
            subprocess.call(qcall + ['subnet-create', 'flat', '{0}'.format(l2_network), '--allocation-pool',
                            'start={0},end={1}'.format(l2_s_address, l2_e_address), '--gateway',
                            '{0}'.format(l2_gate), '--name', 'flat ', '--dns-nameservers', 'list=true',
                            '{0}'.format(flat_dns2), '{0}'.format(flat_dns1)])
        if 'flat1' not in subprocess.check_output(qcall + ['subnet-list']) and l2_port2_enabled:
            subprocess.call(qcall + ['subnet-create', 'flat1', '{0}'.format(l2_network2), '--allocation-pool',
                            'start={0},end={1}'.format(l2_s_address2, l2_e_address2), '--gateway',
                            '{0}'.format(l2_gate2), '--name', 'flat1', '--dns-nameservers', 'list=true',
                            '{0}'.format(flat2_dns2), '{0}'.format(flat2_dns1)])
    except OSError:
        log.error('Error in basic network creation')


def set_hostname(hostname, fqdn, public_ip):
    host = ('s/controller/{0}/g'.format(hostname))
    etc_dir = str(BASEDIR + 'install_scripts/etc/')
    copy((etc_dir + 'hosts.orig'), (etc_dir + 'hosts'))
    copy((etc_dir + 'hostname.orig'), (etc_dir + 'hostname'))
    subprocess.call(['sed', '-i', host, (etc_dir + 'hosts')])
    subprocess.call(['sed', '-i', host, (etc_dir + 'hostname')])

    if fqdn:
        full_hostname = ('s/#placeholder/{0}/g'.format(public_ip + '    ' + hostname + '    ' + hostname + '.' + fqdn))
        subprocess.call(['sed', '-i', full_hostname, (etc_dir + 'hosts')])

#TODO currently doing nothing with api or compute only nodes
netdir = (BASEDIR + 'install_scripts/etc/network/')


def set_addresses(pport, ppaddress, public_network, public_gateway, l2port, l2bridge, l3port, l3bridge, l2_address,
                  l3_address):
    if not dhcp_public and not packer_calls:

        copy((netdir + 'interfaces.orig'), (netdir + 'interfaces'))
        replace((netdir + 'interfaces'), 'primary-port', pport)
        replace((netdir + 'interfaces'), 'primary-address', ppaddress)
        replace((netdir + 'interfaces'), 'primary-mask', public_netmask)
        replace((netdir + 'interfaces'), 'primary-gateway', public_gateway)
        replace((netdir + 'interfaces'), 'pdns', dns1)
        replace((netdir + 'interfaces'), 'sdns', dns2)
        replace((netdir + 'interfaces'), 'fqdn', fqdn)
    else:
        copy((netdir + 'interfaces.dhcp.orig'), (netdir + 'interfaces'))
        replace((netdir + 'interfaces'), 'primary-port', pport)
    replace((netdir + 'interfaces'), 'flatint', l2port)
    #replace((netdir +'interfaces'), 'flat-bridge', l2bridge)
    replace((netdir + 'interfaces'), 'natint', l3port)
    if address_l2_port:
        with open((netdir + '/' + 'interfaces'), 'a') as interfaces:
            interfaces.write('auto ' + l2_bridge_port + '\n')
            interfaces.write('iface ' + l2_bridge_port + ' ' + 'inet static\n')
            interfaces.write('\taddress ' + l2_address + '\n')
            interfaces.write('\tnetmask ' + l2_mask + '\n')
    if packer_calls and vagrant_calls:
        copy((netdir + 'interfaces.vagrant.orig'), (netdir + 'interfaces'))
        replace((netdir + 'interfaces'), 'primary-port', pport)
        if address_l2_port:
            with open((netdir + '/' + 'interfaces'), 'a') as interfaces:
                interfaces.write('auto ' + l2_bridge_port + '\n')
                interfaces.write('iface ' + l2_bridge_port + ' ' + 'inet static\n')
                interfaces.write('\taddress ' + l2_address + '\n')
                interfaces.write('\tnetmask ' + l2_mask + '\n')
        subprocess.call(['sudo', 'cp', '-f', (BASEDIR + 'install_scripts/etc/network/interfaces'),
                         '/etc/network/interfaces'])

def create_ovs_networks():
    subprocess.call(['sudo', 'ovs-vsctl', 'add-br', '{0}'.format(l2_bridge_port)])
    subprocess.call(['sudo', 'ovs-vsctl', 'set', 'bridge','{0}'.format(l2_bridge_port),
                     'other-config:forward-bpdu=true'])
    subprocess.call(['sudo', 'ovs-vsctl', 'add-br', '{0}'.format(l2_bridge_port2)])
    subprocess.call(['sudo', 'ovs-vsctl', 'set', 'bridge','{0}'.format(l2_bridge_port2),
                     'other-config:forward-bpdu=true'])
    subprocess.call(['sudo', 'ovs-vsctl', 'add-br', '{0}'.format(l3_bridge_port)])

    subprocess.call(['sudo', 'ovs-vsctl', 'add-port', '{0}'.format(l2_bridge_port), '{0}'.format(l2_port)])
    subprocess.call(['sudo', 'ovs-vsctl', 'add-port', '{0}'.format(l2_bridge_port2), '{0}'.format(l2_port2)])
    subprocess.call(['sudo', 'ovs-vsctl', 'add-port', '{0}'.format(l3_bridge_port), '{0}'.format(l3_port)])
    # if cariden:
    #     subprocess.call(['sudo', 'ovs-vsctl', 'add-br', 'cariden'])
    #     subprocess.call(['sudo', 'ovs-vsctl', 'set', 'bridge', 'cariden', 'other-config:hwaddr=12:24:48:96:36:14'])

def set_sysctl():
    print ('sysctl')
    subprocess.call(['sudo', 'sed', '-i', 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/g', '/etc/sysctl.conf'])
    if 'net.ipv4.tcp_keepalive_probes=20' in open('/etc/sysctl.conf').read():
        print ('tcp present')
    else:
        copy('/etc/sysctl.conf', '/tmp/sysctl.conf')
        with open('/tmp/sysctl.conf', 'a') as sysfile:
            sysfile.write('''#TCP keepalives
net.ipv4.tcp_keepalive_probes=20
net.ipv4.tcp_keepalive_time=300
net.ipv4.tcp_keepalive_intvl=60
''')
        system(cpstr % {'from': '/tmp/sysctl.conf', 'to': '/etc/sysctl.conf'})
    print ('added keepalive')

# def place_startup_scripts():
#     ##TODO: salt the no horizon html case
#     if not horizon:
#         subprocess.call(['sudo', 'cp', '-f', (BASEDIR + 'install_scripts/index.html'), '/var/www/index.html'])
    # subprocess.call(['sudo', 'cp', '-f', (BASEDIR + 'install_scripts/init.d/50-default.conf'),
    #                  ('/etc/rsyslog.d/50-default.conf')])
    # subprocess.call(
    #     ['sudo', 'cp', '-f', (BASEDIR + 'vinstall.py'), '/usr/local/bin/vinstall'])
    # subprocess.call(['sudo', 'chmod', '755', '/usr/local/bin/vinstall'])

    # system(cpstr % {'from': (BASEDIR + 'install_scripts/init.d/ank-webserver.init'),
    #                 'to': '/etc/init.d/ank-webserver'})
    #system(cpstr % {'from': (BASEDIR + 'install_scripts/init.d/devstack.init'), 'to': '/etc/init.d/devstack'})
    # system(cpstr % {'from': (BASEDIR + 'install_scripts/init.d/tightvnc.init'), 'to': '/etc/init.d/tightvnc'})
    #system(cpstr % {'from': (BASEDIR + 'install_scripts/orig/keystone_token_delete.sh'),
    #                'to': '/usr/local/bin/keystone_token_delete.sh'})
    #subprocess.call(['sudo', 'chmod', '755', '/usr/local/bin/keystone_token_delete.sh'])
    # subprocess.call(['sudo', 'sed', '-i', 's/MYSQLPASS/{0}/g'.format(mypassword),
    #                  '/usr/local/bin/keystone_token_delete.sh'])
    #subprocess.call(['sudo', 'update-rc.d', 'brctl.py', 'defaults'])
    # if cariden:
    #     system(cpstr % {'from': (BASEDIR + 'install_scripts/init.d/rlm.init'), 'to': '/etc/init.d/rlm'})
    # system(cpstr % {'from': (BASEDIR + 'install_scripts/init.d/nova-serialproxy.init'),
    #                 'to': '/etc/init.d/nova-serialproxy'})
    # system(lnstr % {'orig': '/etc/init.d/nova-serialproxy', 'link': '/etc/rc2.d/S98nova-serialproxy'})
    # system(cpstr % {'from': '/opt/stack/nova/nova/console/serial.html', 'to': '/usr/share/nova-serial/serial.html'})
    # subprocess.call(['sudo', 'chmod', '755', '/etc/init.d/nova-serialproxy'])
    # system(cpstr % {'from': '/opt/stack/nova/nova/console/term.js', 'to': '/usr/share/nova-serial/term.js'})
    # system(
    #     cpstr % {'from': (BASEDIR + 'install_scripts/init.d/virl-std.init'), 'to': '/etc/init.d/virl-std'})
    # system(
    #     cpstr % {'from': (BASEDIR + 'install_scripts/init.d/virl-uwm.init'), 'to': '/etc/init.d/virl-uwm'})
    # subprocess.call(
    #     ['sudo', 'chmod', '755', '/usr/local/bin/vinstall'])
         #'/etc/init.d/ank-webserver', '/etc/init.d/virl-std', '/etc/init.d/virl-uwm'])
    #Edit the autonetkit file and move into place
    # replace((BASEDIR + 'install_scripts/orig/autonetkit.cfg'), 'ANKPORT', ank)
    # system(cpstr % {'from': (BASEDIR + 'install_scripts/orig/autonetkit.cfg'),
    #                 'to': '/root/.autonetkit/autonetkit.cfg'})

    #'/etc/init.d/ank-webserver', '/etc/init.d/virl-vmmwsgi', '/etc/init.d/rlm'])
    # if cariden:
    #     system(lnstr % {'orig': '/etc/init.d/rlm', 'link': '/etc/rc2.d/S98rlm'})
    # system(lnstr % {'orig': '/etc/init.d/ank-webserver', 'link': '/etc/rc2.d/S98ank-webserver'})
    # system(lnstr % {'orig': '/etc/init.d/virl-std', 'link': '/etc/rc2.d/S98virl-std'})
    # system(lnstr % {'orig': '/etc/init.d/virl-uwm', 'link': '/etc/rc2.d/S98virl-uwm'})
    #system(lnstr % {'orig': '/etc/init.d/devstack', 'link': '/etc/rc2.d/S97devstack'})
    # if vnc:
    #     system(lnstr % {'orig': '/etc/init.d/tightvnc', 'link': '/etc/rc2.d/S97tightvnc'})

# def setup_vnc():
#     rmtree('/home/virl/.vnc', ignore_errors=True)
#     #mkdir('/home/virl/.vnc', 0700)
#     mkdir('/home/virl/.vnc', 0o700)
#     subprocess.call(['cp', '-f', (BASEDIR + 'install_scripts/orig/xstartup'), '/home/virl/.vnc/xstartup'])
#     subprocess.call(['cp', '-f', (BASEDIR + 'install_scripts/vnc.passwd'), '/home/virl/.vnc/passwd'])
#     subprocess.call(['sudo', 'service', 'tightvnc', 'restart'])


def setup_vmm():
    subprocess.call(['sudo', '-s', (BASEDIR + 'install_scripts/setup_vmmaestro')])


def fix_ntp():
    subprocess.call(['sudo', 'service', 'ntp', 'stop'])
    subprocess.call(['sudo', 'ntpdate', ntp_server])
    if ntp_server == 'ntp.esl.cisco.com':
        subprocess.call(['sudo', 'cp', '-f', (BASEDIR + 'install_scripts/etc/cisco.ntp.conf'), '/etc/ntp.conf'])
    elif ntp_server == 'ntp.ubuntu.com':
        subprocess.call(['sudo', 'cp', '-f', (BASEDIR + 'install_scripts/etc/ubuntu.ntp.conf'), '/etc/ntp.conf'])
    else:
        subprocess.call(['sudo', 'cp', '-f', (BASEDIR + 'install_scripts/etc/generic.ntp.conf'), '/etc/ntp.conf'])
        subprocess.call(['sudo', 'sed', '-i', ('s/= GENERICNTP/= {0}/g'.format(ntp_server)), '/etc/ntp.conf'])
    subprocess.call(['sudo', 'service', 'ntp', 'start'])


def apache_write():

    with open(("/tmp/apache.conf"), "w") as apache:
        apache.write("""Alias /download /var/www/download\n

<Directory \"/var/www/download\">
    Options Indexes FollowSymLinks MultiViews
    IndexOptions NameWidth=*
</Directory>

Alias /doc /var/www/doc

<Directory \"/var/www/doc\">
    Options Indexes FollowSymLinks MultiViews
    IndexOptions NameWidth=*
</Directory>\n

Alias /training /var/www/training

<Directory \"/var/www/training\">
    Options Indexes FollowSymLinks MultiViews
    IndexOptions NameWidth=*
</Directory>\n

Alias /videos /var/www/videos

<Directory \"/var/www/videos\">
    Options Indexes FollowSymLinks MultiViews
    IndexOptions NameWidth=*
</Directory>\n""")
    subprocess.call(['sudo', 'cp', '-f', ('/tmp/apache.conf'),
                         '/etc/apache2/sites-enabled/apache.conf'])


def std_install():
    alter_virlcfg()
    if path.isfile('/tmp/servers.db'):
        subprocess.call(['sudo', '/usr/local/bin/virl_uwm_server', 'init', '-A',
                         'http://{0}:5000/v2.0'.format(public_ip), '-u', 'uwmadmin', '-p', uwmadmin_passwd, '-U', 'uwmadmin',
                         '-P', uwmadmin_passwd, '-T', 'uwmadmin', '-d', '/tmp/servers.db'])
        subprocess.call(['sudo', 'rm', '-rf', '/tmp/servers.db'])
    else:
        subprocess.call(['sudo', '/usr/local/bin/virl_uwm_server', 'init', '-A',
                         'http://{0}:5000/v2.0'.format(public_ip), '-u', 'uwmadmin', '-p', uwmadmin_passwd, '-U', 'uwmadmin',
                         '-P', uwmadmin_passwd, '-T', 'uwmadmin'])
        if guest_account:
            subprocess.call(['sudo', '/usr/local/bin/virl_uwm_server', 'add-user',
                         '-u', 'guest', '-p', 'guest', '-U', 'guest',
                         '-P', 'guest', '-T', 'guest'])

    subprocess.call(['sudo', 'service', 'virl-uwm', 'start'])
    subprocess.call(['sudo', 'service', 'virl-std', 'start'])


def adduser_vmmwsgi(name, password, tenant):
    add_vmmwsgi = ["sudo", "/usr/local/bin/virl_uwm_server", "add-user", "-u", name,
                   "-p", password, "-U", name, "-P", password, "-T", tenant]
    try:
        output = subprocess.call(add_vmmwsgi)
        log.debug(output)
    except Exception:
        log.error('Error in virl user creation')

def User_Creator(user_list, user_list_limited):
    UNET = True
    user_check = subprocess.check_output(kcall + ['user-list'])
    # guest_check = subprocess.check_output(kcall + ['user-list'])
    # if guest_account:
    #     if 'guest' not in guest_check:
    #         adduser_os('guest', 'guest', 'Member', 'guest', instances=100)
    #         sleep(1)
    #         adduser_vmmwsgi('guest', 'guest', 'guest')
    #         Net_Creator('guest', 'guest')
    if user_list:
        for each_user in user_list.split(','):
            (user, password) = each_user.split(':')
            print ('user creation section for user {0}'.format(user))
            subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'virl_core.project_present', user, 'user_password={0}'
                .format(password), 'user_os_password={0}'.format(password)])
            subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'virl_core.user_present', 'name={0}'.format(user),
                             'project={0}'.format(user),'user_password={0}'.format(password), 'role=admin'])
            #print (user_check)
            # if user not in user_check or user == 'guest':
            #     #print (user)
            #     if user == 'flat':
            #         log.debug('flat user no longer allowed')
            #     elif user == 'guest' and not cml:
            #         print 'guest no longer created in user list'
            #         # adduser_os(user, password, 'Member', user, instances=100)
            #         # sleep(1)
            #         # adduser_vmmwsgi(user, password, user)
            #     else:
            #         adduser_os(user, password, 'admin', user, instances=100)
            #         sleep(1)
            #         adduser_vmmwsgi(user, password, user)
            #     if UNET and not (user == 'flat'):
            #         Net_Creator(user, password)
            #     else:
            #         adduser_vmmwsgi(user, password, user)
            #         log.debug('Not creating networks')
            # else:
            #     log.debug('User already exits')
    if user_list_limited:
        for each_limited_user in user_list_limited.split(','):
            (user, password, limit) = each_limited_user.split(':')
            subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'virl_core.project_present', user, 'user_password={0}'
                .format(password), 'user_os_password={0}'.format(password), 'quota_instances={0}'.format(limit)])
        #
        #     if user not in user_check:
        #         adduser_os(user, password, 'Member', user, limit)
        #         sleep(1)
        #         adduser_vmmwsgi(user, password, user)
        #         if UNET and not ( user == 'flat'):
        #             Net_Creator(user, password)
        #         else:
        #             adduser_vmmwsgi(user, password, user)
        #             log.debug('Not creating networks')
        # else:
        #     log.debug('Limited User already exits')
            #if 'flat' not in user_check:
            #    print('flat not in user check')
            #    adduser_os('flat', 'L23jj$$f', 'admin', 'flat', instances=100)
            #    # Intentionally different password since not in user-list
            #    Adduser_Vmmwsgi('flat', 'L23kk$$f', 'flat')
            #    log.debug('fake flat created')

def adduser_os(name, password, role, tenant, instances):
    try:
        #print(name,password,role,tenant,instances)
        subprocess.call(['/usr/local/bin/adduser_openstack', '{0}'.format(name), '{0}'.format(password), 'foo@example.com'
                        , '{0}'.format(role), '{0}'.format(tenant), '{0}'.format(instances)])
    except Exception:
        log.debug('Error in openstack user creation')


def set_vnc_password(vnc_password):
    if not path.exists('/home/virl/.vnc'):
        mkdir('/home/virl/.vnc')
    if vnc_passwd == 'letmein':
        subprocess.call(['cp', '-f', (BASEDIR + 'install_scripts/vnc.passwd'), '/home/virl/.vnc/passwd'])
    else:
        subprocess.call(['cp', '-f', (BASEDIR + 'install_scripts/vnc.passwd'), '/home/virl/.vnc/passwd'])
        _vnc = envoy.run('vncpasswd -f', data=vnc_password, timeout=4)
        _f = open("/home/virl/.vnc/passwd", "w")
        _f.write(_vnc.std_out)
        _f.close()


def setup_vnc():
    rmtree('/home/virl/.vnc', ignore_errors=True)
    #mkdir('/home/virl/.vnc', 0700)
    mkdir('/home/virl/.vnc', 0o700)
    subprocess.call(['cp', '-f', (BASEDIR + 'install_scripts/orig/xstartup'), '/home/virl/.vnc/xstartup'])
    subprocess.call(['cp', '-f', (BASEDIR + 'install_scripts/vnc.passwd'), '/home/virl/.vnc/passwd'])
    subprocess.call(['sudo', 'service', 'tightvnc', 'restart'])


def desktop_icons():
            autostart = '/home/virl/.config/autostart'
            if not path.exists(autostart):
                makedirs('/home/virl/.config/autostart')
            subprocess.call(['sudo', 'chown', '-R', 'virl:virl', '/home/virl/.config'])

#             with open("/home/virl/.config/autostart/kvmchecker.desktop", "w") as kvmchecker:
#                 kvmchecker.write("""[Desktop Entry]
# Name=kvmchecker
# Comment=verify vt-x support
# Exec=/usr/local/bin/kvmchecker
# Hidden=false
# NoDisplay=false
# X-GNOME-Autostart-enabled=true
# Type=Application
# """)
#             subprocess.call(['sudo', 'chmod', 'a+x', '/home/virl/.config/autostart/kvmchecker.desktop'])

#             with open("/home/virl/.config/autostart/wallpaper.desktop", "w") as wallpaper:
#                 wallpaper.write("""[Desktop Entry]
# Name=wallpaper
# Comment=virl desktop image
# Exec=/usr/bin/pcmanfm --set-wallpaper=/home/virl/.virl.jpg
# Hidden=false
# NoDisplay=false
# X-GNOME-Autostart-enabled=true
# Type=Application
# """)
#
#             subprocess.call(['sudo', 'chmod', 'a+x', '/home/virl/.config/autostart/wallpaper.desktop'])
            desktop = '/home/virl/Desktop'
            if not path.exists(desktop):
                mkdir('/home/virl/Desktop')
#             with open("/home/virl/Desktop/Xterm.desktop", "w") as xconf:
#                 xconf.write("""[Desktop Entry]
# Version=1.0
# Name=xterm
# Comment=xterm for folks
# Exec=/usr/bin/xterm
# Icon=/usr/share/icons/Humanity/apps/48/utilities-terminal.svg
# Terminal=false
# Type=Application
# Categories=Utility;Application;
# """)
#             subprocess.call(['sudo', 'chmod', 'a+x', '/home/virl/Desktop/Xterm.desktop'])
#             if not cml:
#                 with open("/home/virl/Desktop/VMMaestro.desktop", "w") as cmlconf:
#                     cmlconf.write("""[Desktop Entry]
# Version=1.0
# Name=VMMaestro
# Comment=VMMaestro for folks
# Exec=/home/virl/VMMaestro-linux/VMMaestro
# Icon=/home/virl/VMMaestro-linux/icon.xpm
# Terminal=false
# Type=Application
# Categories=Utility;Application;
# """)
#                 subprocess.call(['sudo', 'chmod', 'a+x', '/home/virl/Desktop/VMMaestro.desktop'])
#             with open("/home/virl/Desktop/VIRL-rehost.desktop", "w") as vinstallconf:
#                 vinstallconf.write("""[Desktop Entry]
# Version=1.0
# Name=1. Install networking
# Comment=To finish install
# Exec=/usr/local/bin/vinstall rehost
# Icon=/usr/share/icons/gnome/48x48/status/network-wired-disconnected.png
# Terminal=true
# Type=Application
# Categories=Utility;Application;
# """)
#             subprocess.call(['sudo', 'chmod', 'a+x', '/home/virl/Desktop/VIRL-rehost.desktop'])
#             with open("/home/virl/Desktop/VIRL-renumber.desktop", "w") as vchangesconf:
#                 vchangesconf.write("""[Desktop Entry]
# Version=1.0
# Name=3. Install changes
# Comment=Only after setting.ini changes
# Exec=/usr/local/bin/vinstall renumber
# Icon=/usr/share/icons/Humanity/apps/48/gconf-editor.svg
# Terminal=true
# Type=Application
# Categories=Utility;Application;
# """)
#             subprocess.call(['sudo', 'chmod', 'a+x', '/home/virl/Desktop/VIRL-renumber.desktop'])
#             with open("/home/virl/Desktop/Logout.desktop", "w") as vlogoutconf:
#                 vlogoutconf.write("""[Desktop Entry]
# Version=1.0
# Name=LOGOUT
# Comment=To finish install
# Exec=/usr/bin/lubuntu-logout
# Icon=/usr/share/icons/gnome/48x48/status/computer-fail.png
# Terminal=false
# Type=Application
# Categories=Utility;Application;
# """)
#             subprocess.call(['sudo', 'chmod', 'a+x', '/home/virl/Desktop/Logout.desktop'])
#             with open("/home/virl/Desktop/Reboot2.desktop", "w") as vrebootconf:
#                 vrebootconf.write("""[Desktop Entry]
# Version=1.0
# Name=2. REBOOT
# Comment=To reboot
# Exec=sudo /sbin/reboot
# Icon=/usr/share/icons/gnome/48x48/status/computer-fail.png
# Terminal=false
# Type=Application
# Categories=Utility;Application;
# """)
#             subprocess.call(['sudo', 'chmod', 'a+x', '/home/virl/Desktop/Reboot2.desktop'])
#             with open("/home/virl/Desktop/Reboot.desktop", "w") as vrebootconf:
#                 vrebootconf.write("""[Desktop Entry]
# Version=1.0
# Name=4. REBOOT
# Comment=To reboot
# Exec=sudo /sbin/reboot
# Icon=/usr/share/icons/gnome/48x48/status/computer-fail.png
# Terminal=false
# Type=Application
# Categories=Utility;Application;
# """)
#             subprocess.call(['sudo', 'chmod', 'a+x', '/home/virl/Desktop/Reboot.desktop'])
#             with open("/home/virl/Desktop/IP-ADDRESS.desktop", "w") as ipaconf:
#                 ipaconf.write("""[Desktop Entry]
# Version=1.0
# Name=ip-address
# Comment=To see ip address
# Exec=xterm -e "/sbin/ifconfig eth0 | grep inet ;bash"
# Icon=/usr/share/icons/Humanity/apps/logviewer.svg
# Terminal=false
# Type=Application
# Categories=Utility;Application;
# """)
#             subprocess.call(['sudo', 'chmod', 'a+x', '/home/virl/Desktop/IP-ADDRESS.desktop'])
#             with open("/home/virl/Desktop/README.desktop", "w") as readmeconf:
#                 readmeconf.write("""[Desktop Entry]
# Version=1.0
# Name=README
# Comment=Readme for install
# Exec=gedit /home/virl/.README
# Icon=/usr/share/icons/Humanity/apps/48/accessories-dictionary.svg
# Terminal=false
# Type=Application
# Categories=Utility;Application;
# """)
#             subprocess.call(['sudo', 'chmod', 'a+x', '/home/virl/Desktop/README.desktop'])
#             with open("/home/virl/Desktop/Edit-settings.desktop", "w") as settingsconf:
#                 settingsconf.write("""[Desktop Entry]
# Version=1.0
# Name=0. Edit virl.ini
# Comment=To edit virl.ini file
# Exec=sudo gedit /etc/virl.ini
# Icon=/usr/share/icons/Humanity/apps/48/gedit-icon.svg
# Terminal=false
# Type=Application
# Categories=Utility;Application;
# """)
#             subprocess.call(['sudo', 'chmod', 'a+x', '/home/virl/Desktop/Edit-settings.desktop'])
#             if not cml:
#                 with open("/home/virl/Desktop/Videos.desktop", "w") as videosconf:
#                     videosconf.write("""[Desktop Entry]
# Version=1.0
# Name=Video Playlist
# Comment=Icon Details
# Exec=/usr/bin/vlc .Videos.xspf
# Icon=/usr/share/icons/hicolor/48x48/apps/vlc.png
# Terminal=false
# Type=Application
# Categories=Utility;Application;
# """)
#                 subprocess.call(['sudo', 'chmod', 'a+x', '/home/virl/Desktop/Videos.desktop'])
            subprocess.call(['sudo', 'chown', '-R', 'virl:virl', '/home/virl/Desktop'])
            subprocess.call(['mkdir', '-p', '/home/virl/.config/pcmanfm/lubuntu'])
            subprocess.call(['cp', '-f', (BASEDIR + 'install_scripts/orig/desktop-items-0.conf'),
                             '/home/virl/.config/pcmanfm/lubuntu'])


def Net_Creator(user, password):
    qcall = ['neutron', '--os-tenant-name', '{0}'.format(user), '--os-username', '{0}'.format(user), '--os-password',
             '{0}'.format(password), '--os-auth-url=http://localhost:5000/v2.0']
    try:
        if user not in subprocess.check_output(qadmincall + ['net-list']) and not user == 'flat':
            subprocess.call(qcall + ['net-create', '{0}'.format(user)])
            subprocess.call(qcall + ['net-create', '{0}_snat'.format(user)])
        else:
            print('network already exists')

        if user not in subprocess.check_output(qadmincall + ['subnet-list']) and not user == 'flat':
            subprocess.call(qcall + ['subnet-create', '{0}'.format(user), '10.11.12.0/24', '--gateway', '10.11.12.1',
                                     '--dns-nameserver', '10.11.12.1', '--name', '{0}'.format(user)])
            subprocess.call(qcall + ['subnet-create', '{0}_snat'.format(user), '10.11.11.0/24', '--gateway',
                                     '10.11.11.1', '--dns-nameserver', '10.11.11.1', '--name', '{0}_snat'.format(user)])
        else:
            log.warning('subnet already exists')

        if user not in subprocess.check_output(qadmincall + ['router-list']):
            subprocess.call(qcall + ['router-create', '{0}'.format(user)])
            subprocess.call(qcall + ['router-interface-add', '{0}'.format(user), '{0}'.format(user)])
            subprocess.call(qcall + ['router-interface-add', '{0}'.format(user), '{0}_snat'.format(user)])
            subprocess.call(qadmincall + ['router-gateway-set', '{0}'.format(user), 'ext-net'])
        else:
            log.debug('router already exists')

    except:
        log.error('Error in net create')


def domodification(ospassword, mypassword, ks_token):
    try:
        # copy((BASEDIR + 'install_scripts/orig/do.sh.orig'), (BASEDIR + 'install_scripts/do.sh'))
        copy((BASEDIR + 'install_scripts/orig/index.html.orig'), (BASEDIR + 'install_scripts/index.html'))
        # copy((BASEDIR + 'install_scripts/orig/alter.sh.orig'), (BASEDIR + 'install_scripts/alter.sh'))
        copy((BASEDIR + 'install_scripts/orig/bashrc.orig'), (BASEDIR + 'install_scripts/bashrc'))

    except subprocess.CalledProcessError as err:
        log.error('cp of do and bashrc failed', err)
    try:
        replace(BASEDIR + 'install_scripts/index.html', 'UWMPORT', uwm_port)
        replace(BASEDIR + 'install_scripts/do.sh', 'ospassword', ospassword)
        replace(BASEDIR + 'install_scripts/do.sh', 'mypassql', mypassword)
        # replace(BASEDIR + 'install_scripts/alter.sh', 'ospassword', ospassword)
        # replace(BASEDIR + 'install_scripts/alter.sh', 'mypassql', mypassword)
        replace(BASEDIR + 'install_scripts/bashrc', 'ospassword', ospassword)
        replace(BASEDIR + 'install_scripts/bashrc', 'kstoken', ks_token)
        # replace(BASEDIR + 'install_scripts/openstack', 'ospassword', ospassword)
        # replace(BASEDIR + 'install_scripts/do.sh', 'kstoken', ks_token)
        # replace(BASEDIR + 'install_scripts/alter.sh', 'kstoken', ks_token)
        # replace(BASEDIR + 'install_scripts/openstack', 'kstoken', ks_token)
        # replace(BASEDIR + 'install_scripts/extra', 'WHICHROLE', virl_type)
        # if cml:
        #     replace(BASEDIR + 'install_scripts/extra', 'WHICHRELEASE', 'cml')
        # else:
        #     replace(BASEDIR + 'install_scripts/extra', 'WHICHRELEASE', 'virl')
        subprocess.call(['sed', '-i', ('s/--port .*/--port {0}"/g'.format(ank)),
                         (BASEDIR + 'install_scripts/init.d/ank-webserver.init')])
        copy((BASEDIR + 'install_scripts/bashrc'), ( '/home/virl/.bashrc'))
        copy((BASEDIR + 'install_scripts/bash.profile'), ( '/home/virl/.bash_profile'))
    except subprocess.CalledProcessError as err:
        log.error('proxy sed do FAIL', err)

def call_salt(slsfile):
    print 'Please be patient file {slsfile} is running'.format(slsfile=slsfile)
    subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', slsfile])
    sleep(5)

if __name__ == "__main__":

    varg = docopt(__doc__, version='vinstall .1')
    if varg['zero']:
        if proxy:
            subprocess.call(['sudo', 'env', 'https_proxy={0}'.format(http_proxy),
                             '{0}install_scripts/install_salt.sh'.format(BASEDIR)])
        else:
            subprocess.call(['sudo', '{0}install_scripts/install_salt.sh'.format(BASEDIR)])
        sleep(10)
        building_salt_extra()
        subprocess.call(['sudo', 'rm', '/etc/apt/sources.list.d/saltstack*'])
        for i in range(20):
            print '*'*50
        print ' Your salt key needs to be accepted by salt master before continuing\n'
        print ' You can test with salt-call test.ping for ok result'

    if varg['first']:
        for _each in ['zero', 'host', 'first','ntp']:
            call_salt(_each)
        print 'Please validate the contents of /etc/network/interfaces before rebooting!'
    # if varg['second'] or varg['all']:
    #     # for _each in ['zero','first','host']:
    #     call_salt('first')
    #     # subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'zero'])
    #     # subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'first'])
    #     # subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'host'])

    if varg['second'] or varg['all']:
        for _each in ['mysql-install','rabbitmq-install','keystone-install','keystone-setup','keystone-setup',
                      'keystone-endpoint','osclients','openrc','glance-install','neutron-install']:
            call_salt(_each)

    if varg['third'] or varg['all']:
        if cinder:
            call_salt('cinder-install')
            # subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'cinder-install'])
            if cinder_file:
                subprocess.call(['sudo', '/bin/dd', 'if=/dev/zero', 'of={0}'.format(cinder_loc), 'bs=1M',
                                 'count={0}'.format(cinder_size)])
                subprocess.call(['sudo', '/sbin/losetup', '-f', '--show', '{0}'.format(cinder_loc)])
                subprocess.call(['sudo', '/sbin/pvcreate', '/dev/loop0'])
                subprocess.call(['sudo', '/sbin/vgcreate', 'cinder-volumes', '{0}'.format(cinder_loc)])
            elif cinder_device:
                subprocess.call(['sudo', '/sbin/pvcreate', '{0}'.format(cinder_loc)])
                subprocess.call(['sudo', '/sbin/vgcreate', 'cinder-volumes', '{0}'.format(cinder_loc)])
            else:
                print 'No cinder file or drive created'


        if horizon:
            call_salt('dash-install')
            # subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'dash-install'])
            # sleep(5)

        admin_tenid = (subprocess.check_output(['/usr/bin/keystone --os-tenant-name admin --os-username admin'
                                            ' --os-password {ospassword} --os-auth-url=http://localhost:5000/v2.0'
                                            ' tenant-list | grep -w "admin" | cut -d "|" -f2'
                                           .format(ospassword=ospassword)], shell=True)[1:33])
        service_tenid = (subprocess.check_output(['/usr/bin/keystone --os-tenant-name admin --os-username admin'
                                            ' --os-password {ospassword} --os-auth-url=http://localhost:5000/v2.0'
                                            ' tenant-list | grep -w "service" | cut -d "|" -f2'
                                           .format(ospassword=ospassword)], shell=True)[1:33])
        # print admin_tenid
        subprocess.call(['sudo', 'crudini', '--set','/etc/neutron/neutron.conf', 'DEFAULT',
                         'nova_admin_tenant_id', service_tenid])
        subprocess.call(['sudo', 'crudini', '--set','/etc/salt/minion.d/openstack.conf', '',
                         'keystone.tenant_id', (' ' + admin_tenid)])
        if neutron_switch == 'openvswitch':
            create_ovs_networks()
        create_basic_networks()
    if varg['third'] or varg['all']:
        call_salt('nova-install')
        # subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'nova-install'])
        # sleep(5)
        building_salt_extra()
        sleep(5)
        call_salt('neutron_changes')
        # subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'neutron_changes'])
        # place_startup_scripts()
        apache_write()
        if vnc:
            subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'tightvncserver'])
            if not vnc_passwd == 'letmein':
                set_vnc_password(vnc_passwd)
            sleep(5)
        if heat:
            call_salt('heat-install')
            # subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'heat-install'])
            # sleep(5)

    if varg['fourth'] or varg['all']:
        subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'std'])
        sleep(5)
        subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'ank'])
        if guest_account:
            call_salt('guest')
        # std_install()
        User_Creator(user_list, user_list_limited)
        print ('You need to restart now')
    if varg['test']:
        print 'testing'
    if varg['compute']:
        if not controller:
            subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'nova_compute'])
            subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'neutron_compute'])
    if desktop:
        if varg['desktop']:
            subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'desktop'])
            # _xterm = 'xterm -e %s'
            # subprocess.call(['sudo', 'crudini', '--set','/home/virl/.config/libfm/libfm.conf', 'config', 'terminal',
            #                  _xterm ])
            # subprocess.call(['sudo', 'crudini', '--set','/etc/xdg/lubuntu/libfm/libfm.conf', 'config', 'terminal',
            #                  _xterm ])
            # subprocess.call(['sudo', 'crudini', '--set','/etc/lightdm/lightdm.conf.d/20-lubuntu.conf',
            #          'SeatDefaults', 'allow-guest', ' False'])
            # desktop_icons()

            sleep(5)
        if onedev:
            subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'onepk-external'])
            sleep(5)
    if varg['rehost']:
        '''rehost resets ip addresses of the host itself, resets the clock to deal with drift

        '''
        building_salt_extra()
        sleep(5)
        print "please wait - this may take 30 minutes to complete"
        #call_salt('host')
        #call_salt('ntp')
        subprocess.call(['sudo', 'salt-call', '--local', '-l', 'quiet', 'state.sls', 'host'])
        subprocess.call(['sudo', 'salt-call', '--local', '-l', 'quiet', 'state.sls', 'ntp'])
        ##TODO lets just do all here and be done with it
        #alter_virlcfg()
        #subprocess.call(['sudo', 'rabbitmqctl', 'change_password', 'guest', ospassword])
        # subprocess.call(['sudo', 'service', 'ntp', 'stop'])
        # subprocess.call(['sudo', 'ntpdate', ntp_server])
        # subprocess.call(['sudo', 'service', 'ntp', 'start'])
        #fix_ntp()
        pass
    if varg['password']:
        k_delete_list = (subprocess.check_output( ['keystone --os-username admin --os-password {0}'
                                                       ' --os-tenant-name admin'
                                                       ' --os-auth-url=http://localhost:5000/v2.0 endpoint-list'
                                                       ' | grep -w "regionOne" | cut -d "|" -f2'.format(ospassword)],
                                                     shell=True)).split()
        for _keach in k_delete_list:
            subprocess.call(kcall + ['endpoint-delete', '{0}'.format(_keach)])
        for _each in ['password_change','rabbitmq-install','keystone-install','keystone-setup','keystone-setup',
                      'keystone-endpoint','osclients','openrc','glance-install','neutron-install','cinder-install',
                      'dash-install','nova-install','neutron-changes','std','ank']:
            call_salt(_each)

    if varg['images']:
        call_salt('routervms')
    if varg['renumber']:
        '''renumber fixes initial os nets and services list only'''
        qcall = ['neutron', '--os-tenant-name', 'admin', '--os-username', 'admin', '--os-password',
                 '{0}'.format(ospassword), '--os-auth-url=http://localhost:5000/v2.0']
        nmcall = ['nova-manage', '--os-tenant-name', 'admin', '--os-username', 'admin', '--os-password',
                 '{0}'.format(ospassword), '--os-auth-url=http://localhost:5000/v2.0']
        subprocess.call(['sudo', 'rabbitmqctl', 'change_password', 'guest', ospassword])
        sleep(15)
        nova_services_hosts = ["'ubuntu'"]
        nova_service_list = ["nova-compute","nova-cert","nova-consoleauth","nova-scheduler","nova-conductor"]
        if not hostname == 'virl':
            nova_services_hosts.append("'virl'")
            q_delete_list = (subprocess.check_output( ['neutron --os-username admin --os-password {0}'
                                                       ' --os-tenant-name admin'
                                                       ' --os-auth-url=http://localhost:5000/v2.0 agent-list'
                                                       ' | grep -w "virl" | cut -d "|" -f2'.format(ospassword)],
                                                     shell=True)).split()
            for _qeach in q_delete_list:
                subprocess.call(qcall + ['agent-delete', '{0}'.format(_qeach)])
        # for _each in nova_services_hosts:
        print ('Deleting Nova services for old hostnames')
        subprocess.call(['sudo', 'mysql', '-uroot', '-p{0}'.format(mypassword), 'nova',
                          '--execute=delete from compute_nodes'])
        subprocess.call(['sudo', 'mysql', '-uroot', '-p{0}'.format(mypassword), 'nova',
                         '--execute=delete from services'])
        # for _neach in nova_service_list:
        #   subprocess.call(nmcall + ['service disable --host virl --service {0}'.format(_neach)])
        subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'virl_core.project_absent', 'name=guest'])
        # subprocess.call(qcall + ['router-gateway-clear', 'guest'])
        # subprocess.call(qcall + ['router-interface-delete', 'guest', 'guest'])
        # subprocess.call(qcall + ['router-interface-delete', 'guest', 'guest_snat'])
        # subprocess.call(qcall + ['router-delete', 'guest'])
        # subprocess.call(qcall + ['subnet-delete', 'guest'])
        # subprocess.call(qcall + ['subnet-delete', 'guest_snat'])
        # subprocess.call(qcall + ['net-delete', 'guest'])
        # subprocess.call(qcall + ['net-delete', 'guest_snat'])
        subprocess.call(qcall + ['subnet-delete', 'flat'])
        subprocess.call(qcall + ['subnet-delete', 'flat1'])
        subprocess.call(qcall + ['subnet-delete', 'ext-net'])

        create_basic_networks()
        subprocess.call(['sudo', 'salt-call', '-l', 'quiet', 'state.sls', 'neutron_changes'])
        call_salt('renum')
        if not vnc_passwd == 'letmein':
            set_vnc_password(vnc_passwd)
        if RAMDISK:
            # subprocess.call(['sudo', '-s', (BASEDIR + 'install_scripts/vsetup_ramdisk')])
            call_salt('nova-install')
        User_Creator(user_list, user_list_limited)
        call_salt('guest')
        # if guest_account:
        #     Net_Creator('guest','guest')
        # else:
        #     subprocess.call(['sudo', 'virl_uwm_client', 'project-delete', '--name', 'guest'])

        #subprocess.call(['sudo', 'service', 'networking', 'restart'])
        subprocess.call(['rm', '/home/virl/Desktop/Edit-settings.desktop'])
        subprocess.call(['rm', '/home/virl/Desktop/Reboot2.desktop'])
        subprocess.call(['rm', '/home/virl/Desktop/VIRL-rehost.desktop'])
        subprocess.call(['rm', '/home/virl/Desktop/VIRL-renumber.desktop'])
        subprocess.call(['rm', '/home/virl/Desktop/README.desktop'])
        print ('You need to restart now')
        sleep(30)

    if varg['salt']:
        building_salt_extra()
    if varg['wrap']:
        sshdir = '/home/virl/.ssh'
        if not path.exists(sshdir):
            mkdir(sshdir)
        if vagrant_keys or vagrant_calls:
            copy((BASEDIR + 'orig/authorized_keys2'), ('/home/virl/.ssh/authorized_keys2'))
            copy((BASEDIR + 'orig/authorized_keys'), ('/home/virl/.ssh/authorized_keys'))
        # if cml:
        #     subprocess.call(['cp', '-f', (BASEDIR + 'cml.settings.ini'), '/home/virl/settings.ini'])
        #     #subprocess.call(['sed', '-i', 's/cml = False/cml = True/g', '/home/virl/settings.ini'])
        # else:
        #     subprocess.call(['cp', '-f', (BASEDIR + 'vsettings.ini'), '/home/virl/settings.ini'])

    if path.exists('/tmp/install.out'):
        subprocess.call(['sudo', 'rm', '/tmp/install.out'])