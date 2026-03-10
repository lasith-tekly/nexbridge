import type { TransformResponse } from '@/types/nexbridge.types';
import { mockGoResponse } from '@/mocks/transformResponse';

const API_BASE_URL = 'http://localhost:8000';

export const nexbridgeApi = {
  transform: async (
    xmlPayload: string,
    targetSchema: object
  ): Promise<TransformResponse> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(mockGoResponse);
      }, 2000);
    });
  },

  getRegistry: async (): Promise<{ fields: Record<string, number> }> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          fields: {
            MTOW: 1,
            ZFW: 1,
            FLT_NUM: 2,
            DEPARTURE_TIME: 2,
            ARRIVAL_TIME: 3,
            PASSENGER_COUNT: 3,
            AIRLINE_CODE: 4,
            AIRCRAFT_TYPE: 4
          }
        });
      }, 500);
    });
  },

  healthCheck: async (): Promise<{ status: string; version: string }> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          status: 'healthy',
          version: '1.0.0'
        });
      }, 300);
    });
  }
};
