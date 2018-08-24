#!/usr/bin/env python

import sys
import click
import requests


@click.group()
@click.option("-m", "--module",
              type = str,
              default = "nullpower",
              help = "Name of power manager module")
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
def cli(ctx, module, address, username, password):
    """A command line tool for controlling NP05B power strips, via IP address.
    """
    if ctx.obj is None:
        ctx.obj = {}    
    mod = __import__(module)
    ctx.obj["manager"] = mod.__dict__[module](address, username, password)


@cli.command()
@click.argument("outlet",
                type = click.IntRange(1,16))
@click.pass_context
def power_on(ctx, outlet):
    """Power on specified outlet."""
    response = ctx.obj["manager"].power_on(outlet)
    sys.exit(response)


@cli.command()
@click.argument("outlet",
                type = click.IntRange(1,16))
@click.pass_context
def power_off(ctx, outlet):
    """Power off specified outlet."""    
    response = ctx.obj["manager"].power_off(outlet)
    sys.exit(response)
 

@cli.command()
@click.pass_context
def all_on(ctx):
    """Power on all outlets."""    
    response = ctx.obj["manager"].all_on() 
    sys.exit(response)   
    

@cli.command()
@click.pass_context
def all_off(ctx):
    """Power off all outlets."""    
    response = ctx.obj["manager"].all_off()  
    sys.exit(response)       

@cli.command()
@click.argument("outlet",
                type = click.IntRange(1,16))
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
