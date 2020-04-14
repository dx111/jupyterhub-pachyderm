import { Widget } from '@lumino/widgets';
import { requestAPI } from '../api';
import {ReactWidget} from '@jupyterlab/apputils';
import Dag from '../components/Dag';
import React from 'react'

export async function createDag(): Promise<Widget> {
    try {
      const data = await requestAPI<any>('dag');
      const widget = ReactWidget.create(
        <Dag data={data} width={1300} height={700}></Dag>
      )
      widget.id = 'pachyderm-dag-widget';
      widget.title.label = 'Pachyderm DAG';
      widget.title.closable = true;
      return widget;
    } catch (err) {
      console.error(
        `The pachyderm-jupyterlab-extension server extension appears to be missing.\n${err}`
      );
    }
  }
