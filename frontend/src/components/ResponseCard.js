// src/components/ResponseCard.js

import React from 'react';
import { MessageSquare } from 'lucide-react';
import { motion } from 'framer-motion';

const ResponseCard = ({ responses, movie }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
    className="bg-white rounded-lg shadow-lg p-6 mt-6"
  >
    <div className="flex flex-col space-y-4">
      {responses.map((msg, index) => (
        <div key={index} className="flex items-start">
          <MessageSquare className="h-6 w-6 text-purple-600 mr-3 mt-1" />
          <div>
            <h3 className="text-lg font-semibold mb-2">
              {msg.role === 'assistant' ? 'Respuesta' : 'Usuario'}
            </h3>
            <p className="text-gray-600">{msg.content}</p>
          </div>
        </div>
      ))}
      {movie && (
        <motion.div
          className="mt-4 flex items-center space-x-4"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <motion.img
            src={movie.image_url}
            alt={movie.title}
            className="w-24 h-36 object-cover rounded-lg shadow-md"
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = `${process.env.REACT_APP_BACKEND_URL}/images/default.jpg`; // Ensure default.jpg exists
            }}
          />
          <div>
            <h2 className="text-xl font-bold">{movie.title}</h2>
            <p className="text-gray-700">{movie.description}</p>
          </div>
        </motion.div>
      )}
    </div>
  </motion.div>
);

export default ResponseCard;
