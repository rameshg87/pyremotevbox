========================
Python Remote VirtualBox
========================

Python module to communicate with a remote virtualbox over webservice.

Some examples::

  $ python
  Python 2.7.6 (default, Mar 22 2014, 22:59:38)
  [GCC 4.8.2] on linux2
  Type "help", "copyright", "credits" or "license" for more information.
  >>> import pyremotevbox
  >>> host = pyremotevbox.VirtualBoxHost('10.0.2.2')
  >>> bm1 = host.find_vm('baremetal1')
  >>> bm1.get_power_status()
  'PoweredOff'
  >>> bm1.start()
  >>> bm1.get_power_status()
  'Running'
  >>> bm1.stop()
  >>> bm1.get_power_status()
  'PoweredOff'
  >>> bm1.get_boot_device()
  'Network'
  >>> bm1.set_boot_device(pyremotevbox.DEVICE_DISK)
  >>> bm1.get_boot_device()
  'HardDisk'
  >>> bm1.set_boot_device(pyremotevbox.DEVICE_NETWORK)
  >>> bm1.get_boot_device()
  'Network'
  >>>
  $

