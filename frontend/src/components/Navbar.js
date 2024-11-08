// src/components/Navbar.js

import React, { useState } from 'react';
import { X, Menu, Film, Github } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="fixed w-full z-50 bg-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16">
          {/* Sección de Logo */}
          <div className="flex items-center">
            <Film className="h-8 w-8 text-purple-600" />
            <span className="ml-2 text-xl font-bold">MovieMind</span>
          </div>

          {/* Menú de Escritorio */}
          <div className="hidden md:flex items-center space-x-4">
            <a
              href="https://github.com"
              className="text-gray-600 hover:text-gray-900 transition"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Github className="h-5 w-5" />
            </a>
          </div>

          {/* Botón del Menú Móvil */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="text-gray-600 hover:text-gray-900 focus:outline-none"
              aria-label="Toggle Menu"
            >
              {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Menú Móvil */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-white transition-colors duration-500"
          >
            <div className="px-2 pt-2 pb-3 space-y-1">
              <a
                href="https://github.com"
                className="block px-3 py-2 rounded-md text-gray-600 hover:text-gray-900 transition flex items-center"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Github className="h-5 w-5 inline mr-2" />
                GitHub
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

export default Navbar;
