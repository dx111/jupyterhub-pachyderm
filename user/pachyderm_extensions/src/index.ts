import {
  JupyterFrontEnd, JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { IMainMenu } from '@jupyterlab/mainmenu';
import { Menu } from '@lumino/widgets';
import { ICommandPalette, MainAreaWidget } from '@jupyterlab/apputils';
import { Terminal } from '@jupyterlab/terminal/lib/widget';
import { terminalIcon } from '@jupyterlab/ui-components';

/**
 * Initialization data for pachyderm_extensions.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'pachyderm_extensions',
  autoStart: true,
  requires: [ICommandPalette, IMainMenu],
  activate: (app: JupyterFrontEnd, palette: ICommandPalette, mainMenu: IMainMenu) => {
    console.log('pachyderm_extensions is activated!');

    const addAction = (command, label, executeFn) => {
      // Add the command
      commands.addCommand(command, {
        label: label,
        caption: 'Execute ' + command + ' Command',
        execute: executeFn
      });

      // Add to command palette
      palette.addItem({
        command,
        category: 'Pachyderm',
        args: { origin: 'palette' }
      });

      // Add to the menu
      pachydermMenu.addItem({ command, args: { origin: 'menu' } });
    };

    // Create a menu
    const { commands, serviceManager } = app;
    const pachydermMenu: Menu = new Menu({ commands });
    pachydermMenu.title.label = 'Pachyderm';
    mainMenu.addMenu(pachydermMenu, { rank: 80 });
    
    addAction('pachyderm:shell', 'Shell', async (args) => {
      // adapted from
      // https://github.com/jupyterlab/jupyterlab/blob/master/packages/terminal-extension/src/index.ts
      const name = args['name'] as string;

      const session = await (name
        ? serviceManager.terminals.connectTo({ model: { name } })
        : serviceManager.terminals.startNew());

      const term = new Terminal(session, {
        initialCommand: "pachctl shell"
      });

      term.title.icon = terminalIcon;
      term.title.label = 'pachyderm shell';

      let widget = new MainAreaWidget({ content: term });
      app.shell.add(widget);
      app.shell.activateById(widget.id);
    });
  }
};

export default extension;
