// src/components/StatusIndicator.js

import React from 'react';
import { FaCircle } from 'react-icons/fa';

const StatusIndicator = ({ status }) => {
  return (
    <div className="fixed top-4 right-4 z-50 px-3 py-1 rounded-full flex items-center bg-white shadow-lg">
      <FaCircle color={status === 'online' ? 'green' : 'red'} className="w-3 h-3 mr-2" />
      <span className={status === 'online' ? 'text-green-800' : 'text-red-800'}>
        {status === 'online' ? 'API En Línea' : 'API Fuera de Línea'}
      </span>
    </div>
  );
};

export default StatusIndicator;
