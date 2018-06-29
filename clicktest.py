
import click

import uncursed


@click.command()
@click.option("--name", default="Paul")
def main(name):
    click.echo("Hello {}".format(name))


if __name__ == "__main__":
    main()
