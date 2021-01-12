# vmware2dhcp

`vmware2dhcp` is a Python module which can be used to register virtual machines living
in a VMware infrastructure into a DHCP server using Object Management Application Programming Interface ([OMAPI](https://en.wikipedia.org/wiki/OMAPI)).

## Details

`vmware2dhcp` can be user to help automate the build of virtual machines.

It detects changes in the VMware infrastructure by monitoring virtual machine related events (create, reconfigure, boot and so on...),
parses virtual machines metadata (name, networks, operating system), and register those machines into a DHCP server which serve the PXE boot process.

`vmware2dhcp` only targets virtual machines __having a FQDN based name__. The FQDN name is later used to define a set of dhcp options (host-name, domain-name) while some others dhcp options are simply read from VMware custom attributes (filtered using a user configurable parameter).

Eg: Creating a linux VMware virtual machine named 'foo.bar.com', having a DHCP custom attribute ```dhcp.pxelinux.configfile``` set to ```pxelinux.cfg/anyguest.cfg``` in a monitored VMware 'PROVISIONING_NETWORK' network may result in the following DHCP entry being created:

<!-- markdownlint-disable MD009 -->

```bash
host nh5c9ce4ee55aadcab0440 {
  dynamic;
  hardware ethernet 00:50:56:98:c1:64;
        supersede host-name = "foo";
        supersede domain-name = "bar.com";
        supersede pxelinux.configfile =
                "pxelinux.cfg/anyguest.cfg";
}
```

<!-- markdownlint-enable MD009 -->

## Installation

### As a Docker image

Use the provided Dockerfile to build a Docker image.

<!-- markdownlint-disable MD014 -->

```bash
$ docker build . -t vmware2dhcp
```

<!-- markdownlint-enable MD014 -->

### as a standalone program

Use package manager [pip](https://pip.pypa.io/en/stable/) to install requirements.

```bash
$ pip install -r requirements.txt
Collecting pypureomapi~=0.6 (from -r requirements.txt (line 1))
Collecting pytz~=2018.9 (from -r requirements.txt (line 2))
  Using cached https://files.pythonhosted.org/packages/61/28/1d3920e4d1d50b19bc5d24398a7cd85cc7b9a75a490570d5a30c57622d34/pytz-2018.9-py2.py3-none-any.whl
Collecting pyvmomi~=6.7 (from -r requirements.txt (line 3))
Collecting PyYAML~=5.1 (from -r requirements.txt (line 4))
Collecting six>=1.7.3 (from pyvmomi~=6.7->-r requirements.txt (line 3))
  Using cached https://files.pythonhosted.org/packages/73/fb/00a976f728d0d1fecfe898238ce23f502a721c0ac0ecfedb80e0d88c64e9/six-1.12.0-py2.py3-none-any.whl
Collecting requests>=2.3.0 (from pyvmomi~=6.7->-r requirements.txt (line 3))
  Using cached https://files.pythonhosted.org/packages/7d/e3/20f3d364d6c8e5d2353c72a67778eb189176f08e873c9900e10c0287b84b/requests-2.21.0-py2.py3-none-any.whl
Collecting certifi>=2017.4.17 (from requests>=2.3.0->pyvmomi~=6.7->-r requirements.txt (line 3))
  Using cached https://files.pythonhosted.org/packages/60/75/f692a584e85b7eaba0e03827b3d51f45f571c2e793dd731e598828d380aa/certifi-2019.3.9-py2.py3-none-any.whl
Collecting idna<2.9,>=2.5 (from requests>=2.3.0->pyvmomi~=6.7->-r requirements.txt (line 3))
  Using cached https://files.pythonhosted.org/packages/14/2c/cd551d81dbe15200be1cf41cd03869a46fe7226e7450af7a6545bfc474c9/idna-2.8-py2.py3-none-any.whl
Collecting urllib3<1.25,>=1.21.1 (from requests>=2.3.0->pyvmomi~=6.7->-r requirements.txt (line 3))
  Using cached https://files.pythonhosted.org/packages/62/00/ee1d7de624db8ba7090d1226aebefab96a2c71cd5cfa7629d6ad3f61b79e/urllib3-1.24.1-py2.py3-none-any.whl
Collecting chardet<3.1.0,>=3.0.2 (from requests>=2.3.0->pyvmomi~=6.7->-r requirements.txt (line 3))
  Using cached https://files.pythonhosted.org/packages/bc/a9/01ffebfb562e4274b6487b4bb1ddec7ca55ec7510b22e4c51f14098443b8/chardet-3.0.4-py2.py3-none-any.whl
Installing collected packages: pypureomapi, pytz, six, certifi, idna, urllib3, chardet, requests, pyvmomi, PyYAML
Successfully installed PyYAML-5.1 certifi-2019.3.9 chardet-3.0.4 idna-2.8 pypureomapi-0.8 pytz-2018.9 pyvmomi-6.7.1.2018.12 requests-2.21.0 six-1.12.0 urllib3-1.24.1
08:58 $ python vmare2dhcp/cli.py
$ python vmare2dhcp/cli.py
...
```

### As a Pip module

Use package manager pip to install vmware2dhcp

```bash
$ pip install git+ssh://git@github.com/jeanfabrice/vmware2dhcp
Collecting git+ssh://git@github.com/jeanfabrice/vmware2dhcp
  Cloning ssh://git@github.com/jeanfabrice/vmware2dhcp to /private/var/folders/4b/fn1pv0554gg_6qf1rz5zzxrh0000gq/T/pip-req-build-4ct_j_e5
Collecting pypureomapi~=0.6 (from vmware2dhcp==0.0.1)
Collecting pytz~=2018.9 (from vmware2dhcp==0.0.1)
  Using cached https://files.pythonhosted.org/packages/61/28/1d3920e4d1d50b19bc5d24398a7cd85cc7b9a75a490570d5a30c57622d34/pytz-2018.9-py2.py3-none-any.whl
Collecting pyvmomi~=6.7 (from vmware2dhcp==0.0.1)
Collecting PyYAML~=5.1 (from vmware2dhcp==0.0.1)
Collecting requests>=2.3.0 (from pyvmomi~=6.7->vmware2dhcp==0.0.1)
  Using cached https://files.pythonhosted.org/packages/7d/e3/20f3d364d6c8e5d2353c72a67778eb189176f08e873c9900e10c0287b84b/requests-2.21.0-py2.py3-none-any.whl
Collecting six>=1.7.3 (from pyvmomi~=6.7->vmware2dhcp==0.0.1)
  Using cached https://files.pythonhosted.org/packages/73/fb/00a976f728d0d1fecfe898238ce23f502a721c0ac0ecfedb80e0d88c64e9/six-1.12.0-py2.py3-none-any.whl
Collecting certifi>=2017.4.17 (from requests>=2.3.0->pyvmomi~=6.7->vmware2dhcp==0.0.1)
  Using cached https://files.pythonhosted.org/packages/60/75/f692a584e85b7eaba0e03827b3d51f45f571c2e793dd731e598828d380aa/certifi-2019.3.9-py2.py3-none-any.whl
Collecting idna<2.9,>=2.5 (from requests>=2.3.0->pyvmomi~=6.7->vmware2dhcp==0.0.1)
  Using cached https://files.pythonhosted.org/packages/14/2c/cd551d81dbe15200be1cf41cd03869a46fe7226e7450af7a6545bfc474c9/idna-2.8-py2.py3-none-any.whl
Collecting chardet<3.1.0,>=3.0.2 (from requests>=2.3.0->pyvmomi~=6.7->vmware2dhcp==0.0.1)
  Using cached https://files.pythonhosted.org/packages/bc/a9/01ffebfb562e4274b6487b4bb1ddec7ca55ec7510b22e4c51f14098443b8/chardet-3.0.4-py2.py3-none-any.whl
Collecting urllib3<1.25,>=1.21.1 (from requests>=2.3.0->pyvmomi~=6.7->vmware2dhcp==0.0.1)
  Using cached https://files.pythonhosted.org/packages/62/00/ee1d7de624db8ba7090d1226aebefab96a2c71cd5cfa7629d6ad3f61b79e/urllib3-1.24.1-py2.py3-none-any.whl
Building wheels for collected packages: vmware2dhcp
  Building wheel for vmware2dhcp (setup.py) ... done
  Stored in directory: /private/var/folders/4b/fn1pv0554gg_6qf1rz5zzxrh0000gq/T/pip-ephem-wheel-cache-ooo_kk_g/wheels/d7/21/6c/6855b2d6bb41266bd63326ce281e82bfa2c5401ddc57eacfbc
Successfully built vmware2dhcp
Installing collected packages: pypureomapi, pytz, certifi, idna, chardet, urllib3, requests, six, pyvmomi, PyYAML, vmware2dhcp
Successfully installed PyYAML-5.1 certifi-2019.3.9 chardet-3.0.4 idna-2.8 pypureomapi-0.8 pytz-2018.9 pyvmomi-6.7.1.2018.12 requests-2.21.0 six-1.12.0 urllib3-1.24.1 vmware2dhcp-0.0.1
$
```

## Usage

### Usage as a Docker image

<!-- markdownlint-disable MD014 -->

```bash
$ docker run vmware2dhcp
```

<!-- markdownlint-enable MD014 -->

### Usage as a standalone Python program

`vmware2dhcp` requires Python 3.

<!-- markdownlint-disable MD014 -->

```bash
$ python ./vmware2dhcp/cli.py
```

<!-- markdownlint-enable MD014 -->

### Usage as a Python Pip module

`vmware2dhcp` requires Python 3.

```bash
$ python
Python 3.7.1 (default, Oct 21 2018, 09:01:26)
[Clang 10.0.0 (clang-1000.11.45.2)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> from vmware2dhcp import Vmware2dhcp
>>> cfg={
...   'dhcp_address': 'localhost',
...   'dhcp_group': ''
...   'dhcp_key_name': 'omapi_key',
...   'dhcp_key_value': 'REVGQVVMVF9ESENQX0tFWV9WQUxVRQ==',
...   'dhcp_port': 7991,
...   'vc_address': 'localhost',
...   'vc_customattribute_dhcpoption_namespace': 'dhcp.',
...   'vc_password': 'password',
...   'vc_username': 'admin',
...   'vm_networks': [],
... }
>>> Vmware2dhcp(cfg).start()
```

For you convenience, the `vmware2dhcp` pip module also include a `vmware-cli` console script, which is a shortcut to the Python `vmware2dhcp/cli.py` Python program.

## Help

```bash
$ python ./vmware2dhcp/cli.py --help
usage: cli.py [-h] [-c CONFIGFILE] [-l LOG_LEVEL]

Populate isc-dhcp-server with VMs living in a VMware environment

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIGFILE, --config CONFIGFILE
                        Config file
  -l LOG_LEVEL, --log-level LOG_LEVEL
                        Set the logging output level: ['CRITICAL', 'ERROR',
                        'WARNING', 'INFO', 'DEBUG']
```

## Configuration

`vmware2dhcp` can be configured using environment variables or a YAML configuration file. Environments variables take precedence over the configuration file.

A [sample config](config.sample.yaml) file is provided.

Environment variables are named accordingly to the configuration file parameters, with a `'V2D'` prefix:

| Configuration file parameter | Environment variable | Default value | Meaning |
|----------|-------------------------|------|-----|
| `dhcp_address` | `V2D_DHCP_ADDRESS` | localhost | address of the DHCP server |
| `dhcp_group` | `V2D_DHCP_GROUP`[^1]| *empty* | target DHCP group for new entries |
| `dhcp_key_name` | `V2D_DHCP_KEY_NAME` | omapi_key | name of the Omapi key configured ont the DHCP server |
| `dhcp_key_value` | `V2D_DHCP_KEY_VALUE` | REVGQVVMVF9ESENQX0tFWV9WQUxVRQ== | value of the Omapi key configured ont the DHCP server |
| `dhcp_port` | `V2D_DHCP_PORT` | 7991 | TCP port of the Opami service exposed by the DHCP server |
| `vc_address` | `V2D_VC_ADDRESS` | localhost | address of the Vcenter to monitor |
| `vc_customattribute_dhcpoption_namespace` | `V2D_VC_CUSTOMATTRIBUTE_DHCPOPTION_NAMESPACE` | dhcp. | namespace to look for VMWare Virtual Machine custom attributes defining DHCP options |
| `vc_password` | `V2D_VC_PASSWORD` | password | password of the vcenter monitoring user |
| `vc_username` | `V2D_VC_USERNAME` | admin | username of for the vcenter monitoring user |
| `vm_networks` | `V2D_VM_NETWORKS`[^3]| *empty* | list of VMware subnet name to monitor |

[^1]: Setting `V2D_DHCP_GROUP` is UNSUPPORTED at the moment. See [Known issues](#dhcp-groups-and-dhcp-supersede-options)

[^2]: vmware2dhcp can register any number of additionals DHCP options into the DHCP server for a particular entry. This is achieved by reading all the VMware custom Virtual Machine attributes, filtering and keeping those having a matching `vc_customattribute_dhcpoption_namespace`, then register the remaining suffix as a DHCP option.

  Eg:
  If your need is to pass the `pxelinux.configfile` dhcp option from VMware to the DHCP server and you already have configured `vc_customattribute_dhcpoption_namespace` to `dhcp.my.company.` then sets your Virtual Machine custom attributes to `dhcp.my.company.pxelinux.configfile=/path/to/pxelinux/configfile`. **Caution** : the type of this VMware custom attributes **must** be of type "Virtual Machine" (*managedObjectType = vim.VirtualMachine*)

[^3]: `V2D_VM_NETWORKS` is a comma separated list of VMware networks. Empty list means 'ALL'

## Monitored events

The following lists of [VMware events](https://vdc-download.vmware.com/vmwb-repository/dcr-public/6b586ed2-655c-49d9-9029-bc416323cb22/fa0b429a-a695-4c11-b7d2-2cbc284049dc/doc/vim.event.VmEvent.html
) are monitored. List may have a different behaviour regarding the DHCP action it runs.

<!-- markdownlint-disable MD033 -->
| VMware event sets | DHCP action |
|----------|-------------------------|
| `vim.event.VmCreatedEvent`<br/>`vim.event.VmReconfiguredEvent`<br/>`vim.event.VmMacChangedEvent`<br/>`vim.event.VmRenamedEvent`<br/>`vim.event.VmPoweredOnEvent`<br/>`vim.event.VmStartingEvent` | Delete DHCP host entry<br/>Create DHCP host entry|
| `vim.event.VmRemovedEvent` | Delete DHCP host entry[^3] |
[^3]: Not implemented. See [Known Issue](#no-host-entry-removal-from-dhcp)
<!-- markdownlint-disable MD033 -->

## Known issues

### DHCP groups and DHCP supersede options

Omapi doesn't allow both group membership and supersede DHCP options to be set for a host entry.
Since `vmware2dhcp` uses supersede DHCP options to register per host domain-name, host-name and pxelinux.config options,
the `dhcp_group` and `V2D_DHCP_GROUP` are not effective at the moment.

### No host entry removal from DHCP

`vmware2dhcp` can't unregister a virtual machine from the DHCP server when it gets deleted from the VMware inventory.
At the time the `vim.event.VmRemovedEvent` is received, the virtual machine has already been deleted
from the Vmware inventory and its mac address is not available anymore.

## Author

Jean-Fabrice  <[github@bobo-rousselin.com](mailto:github@bobo-rousselin.com)>

## License

[MIT](LICENSE)
