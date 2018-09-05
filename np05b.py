#!/usr/bin/env python


import click
import requests
import sys


class NP05B_http(object):
    def __init__(self, address, username = "admin", password = "admin"):
        self.address = address
        self.username = username
        self.password = password
        self.url = "http://{}/cmd.cgi?".format(address)

    def _run_command(self, cmd, args=[]):
        argstr = " ".join([str(i) for i in args])
        fullurl = "{}{} {}".format(self.url, cmd, argstr)
        r = requests.post(fullurl, auth=(self.username, self.password))
        return r

    def all_on(self):
        cmd = "$A7"
        args = [1]
        return self._run_command(cmd, args)

    def all_off(self):       
        cmd = "$A7"
        args = [0]
        return self._run_command(cmd, args)

    def power_on(self, outlet):
        cmd = "$A3"
        args = [outlet, 1]
        return self._run_command(cmd, args)

    def power_off(self, outlet):
        cmd = "$A3"
        args = [outlet, 0]
        return self._run_command(cmd, args)

    def is_on(self, outlet):
        return self.status()[outlet - 1] == 1

    def status(self):
        cmd = "$A5"
        status_str = self._run_command(cmd).content
        return [i for i in reversed([int(c) for c in status_str])]


@click.group()
@click.option("-a", "--address", 
              type = str, 
              default = "192.168.1.100",
              help = "IP address for power manager",
              show_default = True)
@click.option("-u", "--username", 
              type = str, 
              default = "admin",
              help = "Username for power manager",
              show_default = True)
@click.option("-p", "--password", 
              type = str, 
              default = "admin",
              help = "Password for power manager",
              show_default = True)
@click.pass_context
def cli(ctx, address, username, password):
    """A command line tool for controlling NP05B power strips, via IP address.
    """
    if ctx.obj is None:
        ctx.obj = {}    
    ctx.obj["manager"] = NP05B_http(address, username, password)


@cli.command()
@click.argument("outlet",
                type = click.IntRange(1,5))
@click.pass_context
def power_on(ctx, outlet):
    """Power on specified outlet."""
    response = ctx.obj["manager"].power_on(outlet)
    if response.status_code != 200:
        sys.exit(1)


@cli.command()
@click.argument("outlet",
                type = click.IntRange(1,5))
@click.pass_context
def power_off(ctx, outlet):
    """Power off specified outlet."""    
    response = ctx.obj["manager"].power_off(outlet)
    if response.status_code != 200:
        sys.exit(1)    

@cli.command()
@click.pass_context
def all_on(ctx):
    """Power on all outlets."""    
    response = ctx.obj["manager"].all_on()    
    if response.status_code != 200:
        sys.exit(1)    

@cli.command()
@click.pass_context
def all_off(ctx):
    """Power off all outlets."""    
    response = ctx.obj["manager"].all_off()  
    if response.status_code != 200:
        sys.exit(1)         

@cli.command()
@click.argument("outlet",
                type = click.IntRange(1,5))
@click.pass_context
def is_on(ctx, outlet):
    """Return 1 if outlet is on, 0 otherwise."""
    response = ctx.obj["manager"].is_on(outlet)
    if response:
        click.echo("1")
    else:
        click.echo("0")



if __name__ == "__main__":
    cli()
