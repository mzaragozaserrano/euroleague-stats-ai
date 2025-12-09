'use client';

import { useChatStore, ChatSession } from '@/stores/chatStore';
import { Button } from '@/components/ui/button';
import { Plus, Trash2, Edit2, X, MoreVertical, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { useEffect } from 'react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const sessions = useChatStore((state) => state.sessions);
  const currentSessionId = useChatStore((state) => state.currentSessionId);
  const createNewChat = useChatStore((state) => state.createNewChat);
  const loadChat = useChatStore((state) => state.loadChat);
  const deleteChat = useChatStore((state) => state.deleteChat);
  const renameChat = useChatStore((state) => state.renameChat);

  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [hoveredSessionId, setHoveredSessionId] = useState<string | null>(null);

  const handleCreateNewChat = () => {
    createNewChat();
    onClose?.();
  };

  const handleSelectChat = (sessionId: string) => {
    loadChat(sessionId);
    onClose?.();
  };

  const handleStartEditTitle = (session: ChatSession) => {
    setEditingSessionId(session.id);
    setEditingTitle(session.title);
  };

  const handleSaveTitle = (sessionId: string) => {
    if (editingTitle.trim()) {
      renameChat(sessionId, editingTitle.trim());
    }
    setEditingSessionId(null);
    setEditingTitle('');
  };

  const handleDeleteChat = (sessionId: string) => {
    deleteChat(sessionId);
  };

  // Filtrar sesiones para mostrar solo las que tienen contenido (mensajes)
  // Ordenar sesiones por fecha de actualización (más recientes primero)
  const sortedSessions = [...sessions]
    .filter((session) => session.messages.length > 0)
    .sort((a, b) => b.updatedAt - a.updatedAt);

  return (
    <>
      {/* Sidebar Container */}
      <aside
        className={`fixed md:relative top-0 left-0 h-screen w-64 bg-slate-900 dark:bg-slate-950 border-r border-slate-800 flex flex-col transition-transform duration-300 z-40 ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Close Button (Mobile) */}
        <div className="md:hidden p-4 border-b border-slate-800">
          <Button
            onClick={onClose}
            size="sm"
            variant="ghost"
            className="w-full justify-start text-slate-400 hover:text-slate-200"
          >
            <X className="w-4 h-4 mr-2" />
            Cerrar
          </Button>
        </div>

        {/* New Chat Button */}
        <div className="p-4 border-b border-slate-800">
          <Button
            onClick={handleCreateNewChat}
            className="w-full gap-2 bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="w-4 h-4" />
            Nueva conversación
          </Button>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto p-4">
          {sortedSessions.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-slate-500">
                No hay conversaciones. Crea una nueva para comenzar.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {sortedSessions.map((session) => (
                <div
                  key={session.id}
                  onMouseEnter={() => setHoveredSessionId(session.id)}
                  onMouseLeave={() => setHoveredSessionId(null)}
                  className={`group relative rounded-lg transition-colors ${
                    currentSessionId === session.id
                      ? 'bg-slate-800 border border-blue-500/50'
                      : 'bg-slate-800/50 hover:bg-slate-800 border border-transparent'
                  }`}
                >
                  {editingSessionId === session.id ? (
                    // Editing mode
                    <div className="p-3 space-y-2">
                      <input
                        type="text"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        className="w-full px-2 py-1 bg-slate-700 text-white rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Título de la conversación"
                        autoFocus
                      />
                      <div className="flex gap-1">
                        <button
                          onClick={() => handleSaveTitle(session.id)}
                          className="flex-1 px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded"
                        >
                          Guardar
                        </button>
                        <button
                          onClick={() => setEditingSessionId(null)}
                          className="flex-1 px-2 py-1 bg-slate-700 hover:bg-slate-600 text-white text-xs rounded"
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  ) : (
                    // Display mode
                    <button
                      onClick={() => handleSelectChat(session.id)}
                      className="w-full text-left p-3 focus:outline-none"
                      disabled={session.isLoading}
                    >
                      <div className="flex items-center gap-2">
                        {session.isLoading && (
                          <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin flex-shrink-0" />
                        )}
                        <p className="text-sm text-slate-200 font-medium truncate pr-8">
                          {session.title}
                        </p>
                      </div>
                    </button>
                  )}

                  {/* Action buttons (visible on hover) */}
                  {hoveredSessionId === session.id && editingSessionId !== session.id && (
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1">
                      <button
                        onClick={() => handleStartEditTitle(session)}
                        className="p-1.5 bg-slate-700 hover:bg-slate-600 rounded text-slate-300 hover:text-white transition-colors"
                        title="Editar título"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteChat(session.id)}
                        className="p-1.5 bg-slate-700 hover:bg-red-700 rounded text-slate-300 hover:text-white transition-colors"
                        title="Eliminar conversación"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

