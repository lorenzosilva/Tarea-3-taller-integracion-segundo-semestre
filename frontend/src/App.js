// src/App.js

import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import StatusIndicator from './components/StatusIndicator';
import MovieList from './components/MovieList';
import QueryForm from './components/QueryForm';
import ResponseCard from './components/ResponseCard';
import MovieDetails from './components/MovieDetails';
import axios from 'axios';
import { motion } from 'framer-motion';

const App = () => {
  const [movies, setMovies] = useState([]);
  const [responses, setResponses] = useState([]); // Changed from single response to array for chat
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [selectedMovie, setSelectedMovie] = useState(null); // State for selected movie
  const [errorMessage, setErrorMessage] = useState(null); // State for error messages

  // Fetch API status and movies
  useEffect(() => {
    let intervalId;

    const fetchStatus = async () => {
      try {
        const res = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/status`);
        if (res.data.status === 'running') {
          setStatus('online');
          fetchMovies();
          if (intervalId) {
            clearInterval(intervalId);
          }
        } else {
          setStatus('offline');
        }
      } catch (error) {
        setStatus('offline');
      }
    };

    const fetchMovies = async () => {
      try {
        const res = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/movies`);
        setMovies(res.data);
        setSelectedMovie(null); // Reset selected movie
      } catch (error) {
        console.error('Error al obtener películas:', error);
      }
    };

    fetchStatus();

    intervalId = setInterval(fetchStatus, 5000); // Poll every 5 seconds

    return () => clearInterval(intervalId);
  }, []);

  /**
   * Extracts the movie name from the query using partial matching.
   * @param {string} query - The user's query.
   * @param {Array} moviesList - List of available movies.
   * @returns {Object|null} - The matched movie object or null.
   */
  const extractMovieName = (query, moviesList) => {
    const lowerQuery = query.toLowerCase();

    for (let movie of moviesList) {
      const titleWords = movie.title.toLowerCase().split(' ');
      for (let word of titleWords) {
        if (lowerQuery.includes(word)) {
          return movie;
        }
      }
    }
    return null;
  };

  /**
   * Maneja el envío de una consulta.
   * @param {string} query - La consulta del usuario.
   */
  const handleSubmit = async (query) => {
    setLoading(true);
    setErrorMessage(null); // Reset any previous error messages

    let payload = { query };

    if (selectedMovie) {
      // If a movie is selected from the frontend, include it in the payload
      payload.selected_movie = selectedMovie.title;
    } else {
      // Attempt to extract the movie from the query
      const extractedMovie = extractMovieName(query, movies);
      if (extractedMovie) {
        payload.selected_movie = extractedMovie.title;
        setSelectedMovie(extractedMovie); // Update the selected movie state
      } else {
        setSelectedMovie(null); // Reset if no movie is extracted
      }
    }

    try {
      // Make the POST request to the backend with the payload
      const res = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/query`,
        payload,
        { timeout: 600000 } // 10 minutes
      );
      const answer = res.data.answer;

      // Update the responses to display the answer
      setResponses([{ role: 'assistant', content: answer }]);
    } catch (error) {
      console.error('Error al obtener la respuesta:', error);
      // Handle errors appropriately
      if (error.response && error.response.status === 504) {
        setResponses([{ role: 'assistant', content: 'Tiempo de espera agotado. Por favor, intenta de nuevo más tarde.' }]);
        setErrorMessage('Tiempo de espera agotado. Por favor, intenta de nuevo más tarde.');
      } else {
        setResponses([{ role: 'assistant', content: 'Ocurrió un error al procesar tu consulta.' }]);
        setErrorMessage('Ocurrió un error.');
      }
    }

    setLoading(false);
  };

  /**
   * Handles the click event on a movie from the list.
   * @param {Object} movie - The clicked movie object.
   */
  const handleMovieClick = (movie) => {
    setSelectedMovie(movie);
    setResponses([]); // Clear previous responses when a new movie is selected
  };

  return (
    <div className="transition-colors duration-500">
      <div className="min-h-screen bg-gray-50 transition-colors duration-200">
        <Navbar />
        <StatusIndicator status={status} />

        <main className="max-w-7xl mx-auto px-4 pt-24 pb-12">
          <motion.h1
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl font-bold text-center mb-12"
          >
            Preguntas y Respuestas sobre Guiones de Películas
          </motion.h1>

          {status === 'online' ? (
            <div className="grid md:grid-cols-3 gap-6">
              {/* Lista de Películas */}
              <div className="md:col-span-1">
                <MovieList movies={movies} onMovieClick={handleMovieClick} />
              </div>

              {/* Formulario de Consulta y Respuesta */}
              <div className="md:col-span-2">
                <QueryForm
                  onSubmit={handleSubmit}
                  loading={loading}
                  isApiOnline={status === 'online'}
                />
                {/* Mostrar mensaje de carga */}
                {loading && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="bg-yellow-100 text-yellow-800 p-4 rounded-lg text-center mt-6"
                  >
                    <p>Esperando respuesta... (Esto puede tomar mucho tiempo)</p>
                  </motion.div>
                )}
                {/* Mostrar respuestas */}
                {responses.length > 0 && !loading && <ResponseCard responses={responses} movie={selectedMovie} />}
                {/* Mostrar detalles de la película seleccionada */}
                {selectedMovie && <MovieDetails movie={selectedMovie} />}
                {/* Mostrar mensajes de error */}
                {errorMessage && !loading && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="bg-red-100 text-red-800 p-4 rounded-lg text-center mt-6"
                  >
                    <p>{errorMessage}</p>
                  </motion.div>
                )}
              </div>
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="bg-red-100 text-red-800 p-4 rounded-lg text-center transition-colors duration-500"
            >
              <p>La API está fuera de línea. Reintentando cada 5 segundos...</p>
            </motion.div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;