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
  const [responses, setResponses] = useState([]); // Cambiado de una sola respuesta a un array para chat
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [relatedMovie, setRelatedMovie] = useState(null);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [conversationHistory, setConversationHistory] = useState([]); // Nuevo estado para el historial de conversación
  const [errorMessage, setErrorMessage] = useState(null); // Nuevo estado para mensajes de error

  // Obtener el estado de la API y las películas
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
        setSelectedMovie(null); // Reiniciar película seleccionada
      } catch (error) {
        console.error('Error al obtener películas:', error);
      }
    };

    fetchStatus();

    intervalId = setInterval(fetchStatus, 5000); // Consultar cada 5 segundos

    return () => clearInterval(intervalId);
  }, []);

  /**
   * Función para extraer el nombre de la película de la consulta con coincidencia parcial
   * @param {string} query - La consulta del usuario
   * @param {Array} moviesList - Lista de películas disponibles
   * @returns {Object|null} - El objeto de la película coincidente o null
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
   * @param {string} mode - Modo de interacción: 'chat' o 'completion'.
   */
  const handleSubmit = async (query, mode) => {
    setLoading(true);
    setErrorMessage(null); // Reiniciar cualquier mensaje de error previo

    // Extraer el nombre de la película basado en la consulta
    const extractedMovie = extractMovieName(query, movies);
    if (extractedMovie) {
      setSelectedMovie(extractedMovie);
    } else {
      setSelectedMovie(null); // Reiniciar si no hay coincidencia de película
    }

    try {
      // Preparar la carga útil basada en el modo de interacción
      let payload = { query };

      if (mode === 'chat') {
        // Incluir historial de conversación para el modo chat
        payload.conversation_history = conversationHistory;
      }

      // Realizar la solicitud POST al backend con tiempo de espera aumentado
      const res = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/query`,
        payload,
        { timeout: 600000 } // 10 minutos
      );
      const answer = res.data.answer;

      // Manejar la respuesta basada en el modo
      if (mode === 'chat') {
        // Actualizar el historial de conversación
        const newConversation = [
          ...conversationHistory,
          { role: 'user', content: query },
          { role: 'assistant', content: answer },
        ];
        setConversationHistory(newConversation);

        // Actualizar las respuestas para mostrar toda la conversación
        setResponses(newConversation);
      } else {
        // Para el modo completion, mostrar solo la última respuesta
        setResponses([{ role: 'assistant', content: answer }]);
      }
    } catch (error) {
      console.error('Error al obtener la respuesta:', error);
      // Manejar errores de forma adecuada
      if (mode === 'chat') {
        const errorMessage =
          error.response && error.response.status === 504
            ? 'Tiempo de espera agotado. Por favor, intenta de nuevo más tarde.'
            : 'Lo siento, hubo un error al procesar tu solicitud.';
        const newConversation = [
          ...conversationHistory,
          { role: 'user', content: query },
          { role: 'assistant', content: errorMessage },
        ];
        setConversationHistory(newConversation);
        setResponses(newConversation);
      } else {
        const errorMsg =
          error.response && error.response.status === 504
            ? 'Tiempo de espera agotado. Por favor, intenta de nuevo más tarde.'
            : 'Lo siento, hubo un error al procesar tu solicitud.';
        setResponses([{ role: 'assistant', content: errorMsg }]);
      }
      setErrorMessage(
        error.response && error.response.status === 504
          ? 'Tiempo de espera agotado. Por favor, intenta de nuevo más tarde.'
          : 'Ocurrió un error.'
      );
    }

    setLoading(false);
  };

  const handleMovieClick = (movie) => {
    setSelectedMovie(movie);
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
                {responses.length > 0 && !loading && <ResponseCard responses={responses} movie={relatedMovie} />}
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