#! /usr/bin/env python
#
# Hypertable Deployment using Fabric
#   Reference: 
#   https://github.com/nuggetwheat/hypertable/blob/master/conf/Capfile.cluster
#
# @author: Sreejith K
# @date: 14 Oct 2011


from fabric.api import run, local
from fabric.decorators import roles, task
from fabric.network import disconnect_all


INSTALL_DIR             = '/opt/hypertable'
HYPERTABLE_VERSION      = '0.9.5.0'
CONFIG_FILE             = '/etc/cyclozzo/hypertable.config'
CONFIG_OPTION           = '--config=%s/%s/conf/%s'
DEFAULT_DFS             = 'hadoop'


def update_roles(master, slaves):
    """Update the Fabric runtime environment with roles.
    """
    env.roledefs['master'] = master
    env.roledefs['hyperspace'] = master
    env.roledefs['thriftbroker'] = master
    env.roledefs['slave'] = [master] + slaves
    env.roledefs['install'] = slaves


@task
def copy_config(config=CONFIG_FILE,
                install_dir=INSTALL_DIR, 
                hypertable_version=HYPERTABLE_VERSION):
    """Copies config file to installation on localhost.
    """
    local('rsync -e "ssh -o StrictHostKeyChecking=no" %s %s/%s/conf/' 
                            %(config, install_dir, hypertable_version)
                            )


@task
@roles('install')
def rsync(source_machine='127.0.0.1',
          install_dir=INSTALL_DIR,
          hypertable_version=HYPERTABLE_VERSION):
    """rsyncs installation directory to cluster.  For each machine in the
    cluster, his commannd  rsyncs the installation from the source
    installation machine specified by the variable 'source_machine'
    """
    run('rsync -av -e "ssh -o StrictHostKeyChecking=no" --exclude=log ' \
        '--exclude=run --exclude=demo --exclude=fs --exclude=hyperspace/ ' \
        '%s:%s/%s %s'
            %(source_machine, install_dir, hypertable_version, install_dir)
        )
    run('rsync -av -e "ssh -o StrictHostKeyChecking=no" --exclude=log ' \
        '--exclude=run --exclude=demo --exclude=fs --exclude=hyperspace/ ' \
        '%s:%s/%s/conf/ %s/%s/conf'
            %(source_machine, 
              install_dir, 
              hypertable_version, 
              install_dir, 
              hypertable_version
              )
        )


@task
def dist():
    """Distributes installation.  This task copiles the config file and
    then rsyncs the installation to each machine in the cluster.
    """
    copy_config()
    rsync()


@task
@roles('hyperspace')
def start_hyperspace(instll_dir=INSTALL_DIR, config_option=CONFIG_OPTION):
    """Starts hyperspace process
    """
    run('%s/current/bin/start-hyperspace.sh %s'
        % (install_dir, config_option)
        )


@task
@roles('master')
def start_master(instll_dir=INSTALL_DIR,
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


@task
@roles('slave')
def start_slaves(instll_dir=INSTALL_DIR,
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


@task
@roles('master')
def start_master_thriftbroker(instll_dir=INSTALL_DIR,
                              dfs=DFS, 
                              config_option=CONFIG_OPTION):
    """Starts thriftbroker on master.
    """
    run('%s/current/bin/start-thriftbroker.sh %s %s'
        % (install_dir, dfs, config_option)
        )


@task
def start():
    """Start all services.
    """
    start_hyperspace()
    start_master()
    start_slaves()
    start_master_thriftbroker()