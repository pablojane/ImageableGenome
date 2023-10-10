Installation
============

Check out the :doc:`Introduction <intro>` section for information on the pre-requirements before proceeding to install the package.

To install the *imagenome* package using pip, download/clone the repository, open a terminal on its root directory and execute the command

::

    pip install .


Some of the dependencies will be installed by default in your ~/.local/bin directory. If the path to this directory is not included in your PATH environment variable, a warning message will be shown in your terminal during installation. If this is the case, once the installation of *imagenome* and its dependencies is complete, add this directory to your PATH using the terminal command

::

    PATH=$PATH:~/.local/bin

You can make these changes permanent by adding the line above at the end of your ~/.bashrc file. The changes will be made effective once you open a new terminal.


