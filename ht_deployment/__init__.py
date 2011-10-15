#! /usr/bin/env python
#
# Hypertable Deployment using Fabric
#   Reference: 
#   https://github.com/nuggetwheat/hypertable/blob/master/conf/Capfile.cluster
#
# @author: Sreejith K
# @date: 14 Oct 2011


import os
import sys

from fabric.api import run, local, env, settings
from fabric.decorators import roles, task
from fabric.network import disconnect_all


INSTALL_DIR             = '/opt/hypertable'
HYPERTABLE_VERSION      = '0.9.5.0'
CONFIG_FILE             = '/opt/hypertable/production-hypertable.cfg'
CONFIG_OPTION           = '--config=%s/%s/conf/%s' % (INSTALL_DIR,
                                                      HYPERTABLE_VERSION,
                                                      os.path.basename(
                                                            CONFIG_FILE
                                                            )
                                                      )
DFS		                = 'hadoop'


def update_roles(master, slaves):
    """Update the Fabric runtime environment with roles.
    """
    env.roledefs['source'] = [master]
    env.roledefs['master'] = [master]
    env.roledefs['hyperspace'] = [master]
    env.roledefs['thriftbroker'] = [master]
    env.roledefs['slave'] = [master] + slaves
    env.roledefs['install'] = slaves


###############################################################################
# Task definitions for `fab` tool. Use them using `fab <alias>`
###############################################################################


@task(alias='copy_config')
def _copy_config(config=CONFIG_FILE,
                 install_dir=INSTALL_DIR, 
                 hypertable_version=HYPERTABLE_VERSION):
    """Copies config file to installation on localhost.
    """
    local('rsync -e "ssh -o StrictHostKeyChecking=no" %s %s/%s/conf/' 
                            %(config, install_dir, hypertable_version)
                            )


@task(alias='rsync')
@roles('install')
def _rsync(install_dir=INSTALL_DIR,
           hypertable_version=HYPERTABLE_VERSION):
    """rsyncs installation directory to cluster.  For each machine in the
    cluster, his commannd  rsyncs the installation from the source
    installation machine specified by the role 'source'
    """
    run('rsync -av -e "ssh -o StrictHostKeyChecking=no" --exclude=log ' \
        '--exclude=run --exclude=demo --exclude=fs --exclude=hyperspace/ ' \
        '%s:%s/%s %s'
            %(env.roledefs['source'][0], install_dir, hypertable_version, install_dir)
        )
    run('rsync -av -e "ssh -o StrictHostKeyChecking=no" --exclude=log ' \
        '--exclude=run --exclude=demo --exclude=fs --exclude=hyperspace/ ' \
        '%s:%s/%s/conf/ %s/%s/conf'
            %(env.roledefs['source'][0], 
              install_dir, 
              hypertable_version, 
              install_dir, 
              hypertable_version
              )
        )


@task(alias='dist')
@roles('install')
def _dist():
    """Distributes installation.  This task copiles the config file and
    then rsyncs the installation to each machine in the cluster.
    """
    _copy_config()
    _rsync()


@task(alias='start-hyperspace')
@roles('hyperspace')
def _start_hyperspace(install_dir=INSTALL_DIR, config_option=CONFIG_OPTION):
    """Starts hyperspace process
    """
    run('%s/current/bin/start-hyperspace.sh %s'
        % (install_dir, config_option)
        )


@task(alias='stop-hyperspace')
@roles('hyperspace')
def _stop_hyperspace(install_dir=INSTALL_DIR):
    """Stop all hyperspace services
    """
    run( '%s/current/bin/stop-hyperspace.sh' % install_dir)
    

@task(alias='start-master')
@roles('master')
def _start_master(install_dir=INSTALL_DIR,
                  dfs=DFS,
                  config_option=CONFIG_OPTION):
    """Starts master process
    """
    run('%s/current/bin/start-dfsbroker.sh %s %s'
        % (install_dir, dfs, config_option)
        )
    run('%s/current/bin/start-master.sh %s'
        % (install_dir, config_option)
        )
    run('%s/current/bin/start-monitoring.sh %s' %install_dir)


@task(alias='stop-master')
@roles('master')
def _stop_master(install_dir=INSTALL_DIR):
    """Stop hypertable master service
    """
    run('%s/current/bin/stop-servers.sh --no-hyperspace --no-rangeserver ' \
        '--no-dfsbroker' % install_dir
        )
    run('%s/current/bin/stop-monitoring.sh' % install_dir)


@task(alias='start-slaves')
@roles('slave')
def _start_slaves(instll_dir=INSTALL_DIR,
                  dfs=DFS, 
                  config_option=CONFIG_OPTION):
    """Starts all the slave processes.
    """
    run('%s/current/bin/random_wait.sh 5' %install_dir)
    run('%s/current/bin/start-dfsbroker.sh %s %s'
        % (install_dir, dfs, config_option)
        )
    run('%s/current/bin/start-rangeserver.sh %s %s'
        % (install_dir, dfs, config_option)
        )
    run('%s/current/bin/start-thriftbroker.sh %s %s'
        % (install_dir, dfs, config_option)
        )


@task(alias='stop-slaves')
@roles('slave')
def _stop_slaves(install_dir=INSTALL_DIR):
    """Stop all the slave services
    """
    run('%s/current/bin/stop-servers.sh --no-hyperspace --no-master ' \
        '--no-dfsbroker' % install_dir
        )


@task(alias='stop-dfsbrokers')
@roles('master', 'slave')
def _stop_dfsbrokers(install_dir=INSTALL_DIR):
    """Stop all the dfsbrokers
    """
    run('%s/current/bin/stop-hyperspace.sh' % install_dir)


@task(alias='start-master-thriftbroker')
@roles('master')
def _start_master_thriftbroker(instll_dir=INSTALL_DIR,
                               dfs=DFS, 
                               config_option=CONFIG_OPTION):
    """Starts thriftbroker on master.
    """
    run('%s/current/bin/start-thriftbroker.sh %s %s'
        % (install_dir, dfs, config_option)
        )


@task(alias='stop-thriftbroker')
@roles('thriftbroker')
def _stop_thriftbroker(install_dir=INSTALL_DIR):
    """Stop all the thriftbrokers
    """
    run('%s/current/bin/stop-servers.sh --no-hyperspace --no-master ' \
        '--no-rangeserver' % install_dir
        )
    

@task(alias='start')
def _start():
    """Start all services.
    """
    _start_hyperspace()
    _start_master()
    _start_slaves()
    _start_master_thriftbroker()


@task(alias='stop')
def _stop():
    """Stop all services.
    """
    _stop_master()
    _stop_slaves()
    _stop_hyperspace()
    _stop_dfsbrokers()



###############################################################################
# The Following functions can be imported as used in any Python module
###############################################################################


def copy_config(config=CONFIG_FILE,
                install_dir=INSTALL_DIR, 
                hypertable_version=HYPERTABLE_VERSION):
    """Copies config file to installation on localhost.
    """
    _copy_config(config, install_dir, hypertable_version)


def rsync(install_dir=INSTALL_DIR,
          hypertable_version=HYPERTABLE_VERSION):
    """rsyncs installation directory to cluster.  For each machine in the
    cluster, his commannd  rsyncs the installation from the source
    installation machine specified by the role 'source'
    """
    for host in env.roledefs['install']:
        with settings(host_string=host):
            _rsync(install_dir, hypertable_version)


def dist():
    """Distributes installation.  This task copiles the config file and
    then rsyncs the installation to each machine in the cluster.
    """
    copy_config()
    rsync()


def start_hyperspace(install_dir=INSTALL_DIR, config_option=CONFIG_OPTION):
    """Starts hyperspace process
    """
    for host in env.roledefs['hyperspace']:
        with settings(host_string=host):
            _start_hyperspace(install_dir, config_option)


def stop_hyperspace(install_dir=INSTALL_DIR):
    """Stop all hyperspace services
    """
    for host in env.roledefs['hyperspace']:
        with settings(host_string=host):
            _stop_hyperspace(install_dir, config_option)
    

def start_master(instll_dir=INSTALL_DIR,
                 dfs=DFS,
                 config_option=CONFIG_OPTION):
    """Starts master process
    """
    for host in env.roledefs['master']:
        with settings(host_string=host):
            _start_master(instll_dir, dfs, config_option)


def stop_master(install_dir=INSTALL_DIR):
    """Stop hypertable master service
    """
    for host in env.roledefs['master']:
        with settings(host_string=host):
            _stop_master(install_dir)


def start_slaves(instll_dir=INSTALL_DIR,
                  dfs=DFS, 
                  config_option=CONFIG_OPTION):
    """Starts all the slave processes.
    """
    for host in env.roledefs['slave']:
        with settings(host_string=host):
            _start_slaves(install_dir, dfs, config_option)


def stop_slaves(install_dir=INSTALL_DIR):
    """Stop all slave services.
    """
    for host in env.roledefs['slave']:
        with settings(host_string=host):
            _stop_slaves(install_dir)


def stop_dfsbrokers(install_dir=INSTALL_DIR):
    """Stop all dfsbrokers.
    """
    for host in (env.roledefs['master'] +  env.roledefs['slave']):
        with settings(host_string=host):
            _stop_dfsbrokers(install_dir)


def start_master_thriftbroker(instll_dir=INSTALL_DIR,
                              dfs=DFS, 
                              config_option=CONFIG_OPTION):
    """Starts thriftbroker on master.
    """
    for host in env.roledefs['master']:
        with settings(host_string=host):
            _start_master_thriftbroker(install_dir, dfs, config_option)


def stop_thriftbroker(install_dir=INSTALL_DIR):
    """Stop all thriftbrokers.
    """
    for host in env.roledefs['thriftbroker']:
        with settings(host_string=host):
            _stop_thriftbroker(install_dir)
    

def start():
    """Start all services.
    """
    start_hyperspace()
    start_master()
    start_slaves()
    start_master_thriftbroker()


def stop():
    """Stop all services.
    """
    stop_master()
    stop_slaves()
    stop_hyperspace()
    stop_dfsbrokers()

 
if __name__ == '__main__':
    # use as python library
    if len(sys.argv) < 4:
        print 'Usage: ht-deploy <task> <master> <slaves>'
        sys.exit(-1)
    else:
        action = sys.argv[1]
    update_roles(master=sys.argv[2], slaves=sys.argv[3])
    print '--> Running action', action
    globals().get(action, 'dist')()
    disconnect_all()
else:
    # use with fab tool
    update_roles(master='172.16.5.125', slaves=['172.16.5.124'])

