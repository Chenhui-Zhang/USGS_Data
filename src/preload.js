const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('papersprout', {
  ping: () => ipcRenderer.invoke('zotero:ping'),
  collections: () => ipcRenderer.invoke('zotero:collections'),
  items: (key) => ipcRenderer.invoke('zotero:items', key),
  paper: (key) => ipcRenderer.invoke('zotero:paper', key),
  openInZotero: (key) => ipcRenderer.invoke('zotero:open', key)
});
