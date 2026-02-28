import { createContext, useContext } from 'react';
export const SettingsContext = createContext();
export const useSettings = () => useContext(SettingsContext);
