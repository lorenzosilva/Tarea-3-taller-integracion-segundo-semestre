// src/components/MovieList.js

import React from 'react';
import { Film } from 'lucide-react';
import { motion } from 'framer-motion';

const MovieList = ({ movies, onMovieClick }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="bg-white rounded-lg shadow-lg p-6"
  >
    <h2 className="text-xl font-bold mb-4">Películas Disponibles</h2>
    <div className="space-y-2">
      {movies.map((movie, index) => (
        <motion.div
          key={index}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.1 }}
          className="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition cursor-pointer"
          onClick={() => onMovieClick(movie)}
        >
          <Film className="h-5 w-5 text-purple-600 mr-3" />
          <span>{movie.title}</span>
        </motion.div>
      ))}
    </div>
  </motion.div>
);

export default MovieList;
