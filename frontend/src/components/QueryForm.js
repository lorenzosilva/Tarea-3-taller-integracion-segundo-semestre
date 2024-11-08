// src/components/QueryForm.js

import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

const QueryForm = ({ onSubmit, loading, isApiOnline }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(query); // Pass only the query to App.js
    setQuery(''); // Optionally, clear the input after submission
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

      {/* Removed Interaction Mode Selection */}

      <button
        type="submit"
        disabled={!isApiOnline || loading}
        className={clsx(
          'mt-4 w-full bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition disabled:opacity-50',
          { 'cursor-not-allowed': !isApiOnline || loading }
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
