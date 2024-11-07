// src/components/MovieDetails.js

import React from 'react';
import { motion } from 'framer-motion';

const MovieDetails = ({ movie }) => {
  if (!movie) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-lg p-6 mt-6"
    >
      <h3 className="text-lg font-semibold mb-2">
        {movie.title}
      </h3>
      <p className="text-gray-600">{movie.description}</p>
      <motion.img
        src={movie.image_url}
        alt={movie.title}
        className="mt-4 w-full max-w-sm rounded-lg shadow-md"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        onError={(e) => {
          e.target.onerror = null;
          e.target.src = `${process.env.REACT_APP_BACKEND_URL}/images/default.jpg`; // Asegurarse de que default.jpg exista
        }}
      />
    </motion.div>
  );
};

export default MovieDetails;
