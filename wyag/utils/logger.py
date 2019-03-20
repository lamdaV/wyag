import click

class Logger(object):
  def __init__(self, verbose):
    self.verbose = verbose

  def debug(self, message):
    self.log(message, "blue")

  def info(self, message):
    self.log(message, "cyan")

  def warn(self, message):
    self.log(message, "yellow")

  def error(self, message):
    self.log(message, "red")

  def success(self, message):
    self.log(message, "green")

  def log(self, message, color):
    if self.verbose:
      click.secho(message, fg=color)