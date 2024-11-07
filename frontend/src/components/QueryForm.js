// src/components/QueryForm.js

import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

const QueryForm = ({ onSubmit, loading, isApiOnline }) => {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('completion'); // 'chat' o 'completion'

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(query, mode); // Pasar tanto la consulta como el modo a App.js
    setQuery(''); // Opcionalmente, limpiar la entrada después del envío
  };

  return (
    <motion.form
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      onSubmit={handleSubmit}
      className="bg-white rounded-lg shadow-lg p-6"
    >
      <div className="relative">
        <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Pregunta sobre cualquier película..."
          className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent bg-gray-50 text-gray-900"
          disabled={!isApiOnline || loading}
          required
        />
      </div>

      {/* Selección de Modo de Interacción */}
      <div className="mt-4">
        <label className="block text-gray-700">Modo de Interacción:</label>
        <select
          value={mode}
          onChange={(e) => setMode(e.target.value)}
          className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-purple-600 focus:border-purple-600 sm:text-sm rounded-md"
          disabled={!isApiOnline || loading}
        >
          <option value="completion">Completion</option>
          <option value="chat">Chat</option>
        </select>
      </div>

      <button
        type="submit"
        disabled={!isApiOnline || loading}
        className={clsx(
          'mt-4 w-full bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition disabled:opacity-50',
          { 'cursor-not-allowed': !isApiOnline }
        )}
      >
        {loading ? (
          <div className="flex items-center justify-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="h-5 w-5 border-2 border-white border-t-transparent rounded-full"
            />
            <span className="ml-2">Esperando respuesta... (Esto puede tomar mucho tiempo)</span>
          </div>
        ) : (
          'Hacer Pregunta'
        )}
      </button>
    </motion.form>
  );
};

export default QueryForm;
