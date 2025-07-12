import { H3Event } from 'h3';
import { RushDB } from '@rushdb/javascript-sdk';

export const useDb = (event: H3Event) => {
  const { rushdbToken, rushdbBaseUrl } = useRuntimeConfig(event);
  return new RushDB(rushdbToken as string, {
    url: rushdbBaseUrl as string,
  });
};
