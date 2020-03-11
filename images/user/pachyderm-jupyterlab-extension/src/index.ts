import {
  JupyterFrontEnd, JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { IMainMenu } from '@jupyterlab/mainmenu';
import { Menu } from '@lumino/widgets';
import { ICommandPalette } from '@jupyterlab/apputils';

import { DAGWidget } from './dag';

/**
 * Initialization data for the pachyderm-jupyterlab-extension extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'pachyderm-jupyterlab-extension',
  autoStart: true,
  requires: [ICommandPalette, IMainMenu],
  activate: (app: JupyterFrontEnd, palette: ICommandPalette, mainMenu: IMainMenu) => {
    console.log('pachyderm-jupyterlab-extension is activated!');

    const { commands } = app;

    // DAG command
    const command = 'pachyderm:dag-viewer';
    commands.addCommand(command, {
      label: 'DAG',
      caption: 'Execute pachyderm:dag-viewer Command',
      execute: (args) => {
        const widget = new DAGWidget();
        app.shell.add(widget, 'main');
      }
    });

    // Add the command to the command palette
    palette.addItem({
      command,
      category: 'Pachyderm',
      args: { origin: 'palette' }
    });

    // Create a menu
    const pachydermMenu: Menu = new Menu({ commands });
    pachydermMenu.title.label = 'Pachyderm';
    mainMenu.addMenu(pachydermMenu, { rank: 80 });

    // Add the command to the menu
    pachydermMenu.addItem({ command, args: { origin: 'menu' } });
  }
};

export default extension;
