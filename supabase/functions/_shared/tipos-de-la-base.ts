// LOS TIPOS DE LA BASE — ARCHIVO GENERADO. NO SE EDITA A MANO.
//
// Qué es: la forma de las 7 tablas escrita en el idioma de TypeScript, para
// que el editor sepa qué columnas existen, de qué tipo es cada una y cuáles
// pueden venir vacías. Sin esto, TypeScript no tiene de dónde sacarlo y trata
// a cada columna como imposible: por eso `horarios-disponibles` y `reservar`
// daban errores de tipo aun andando bien.
//
// 🔴 ES UNA FOTO Y SE VENCE, igual que la sección 13.9 del documento de
// estado. Dice cómo está la base EL DÍA QUE SE GENERÓ. Cada migración nueva la
// deja un poco más vieja, y una foto vencida es peor que no tenerla porque se
// lee como un hecho verificado.
//
// GENERADA EL 29-ago-2026, contra la base real, con:
//
//   supabase gen types typescript --linked --schema public
//
// ⚠ Ese comando escribe el archivo ENTERO, así que se lleva puesto este
// encabezado: al regenerar hay que volver a pegarlo arriba.
//
// SE REGENERA al aplicar cualquier migración que toque tablas o columnas.
export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.5"
  }
  public: {
    Tables: {
      excepciones: {
        Row: {
          activa: boolean
          created_at: string
          descripcion: string
          fecha_desde: string | null
          fecha_hasta: string | null
          id: number
          profesional_id: number | null
          semana_del_mes: number | null
          tipo: string
        }
        Insert: {
          activa?: boolean
          created_at?: string
          descripcion: string
          fecha_desde?: string | null
          fecha_hasta?: string | null
          id?: number
          profesional_id?: number | null
          semana_del_mes?: number | null
          tipo: string
        }
        Update: {
          activa?: boolean
          created_at?: string
          descripcion?: string
          fecha_desde?: string | null
          fecha_hasta?: string | null
          id?: number
          profesional_id?: number | null
          semana_del_mes?: number | null
          tipo?: string
        }
        Relationships: [
          {
            foreignKeyName: "excepciones_profesional_id_fkey"
            columns: ["profesional_id"]
            isOneToOne: false
            referencedRelation: "profesionales"
            referencedColumns: ["id"]
          },
        ]
      }
      horarios_base: {
        Row: {
          created_at: string
          dia_semana: number
          fin: string
          fin_maximo: string | null
          id: number
          inicio: string
          profesional_id: number
        }
        Insert: {
          created_at?: string
          dia_semana: number
          fin: string
          fin_maximo?: string | null
          id?: number
          inicio: string
          profesional_id: number
        }
        Update: {
          created_at?: string
          dia_semana?: number
          fin?: string
          fin_maximo?: string | null
          id?: number
          inicio?: string
          profesional_id?: number
        }
        Relationships: [
          {
            foreignKeyName: "horarios_base_profesional_id_fkey"
            columns: ["profesional_id"]
            isOneToOne: false
            referencedRelation: "profesionales"
            referencedColumns: ["id"]
          },
        ]
      }
      pacientes: {
        Row: {
          apellido: string
          created_at: string
          dni: string | null
          email: string | null
          fecha_nacimiento: string | null
          id: number
          nombre: string
          telefono: string | null
        }
        Insert: {
          apellido: string
          created_at?: string
          dni?: string | null
          email?: string | null
          fecha_nacimiento?: string | null
          id?: number
          nombre: string
          telefono?: string | null
        }
        Update: {
          apellido?: string
          created_at?: string
          dni?: string | null
          email?: string | null
          fecha_nacimiento?: string | null
          id?: number
          nombre?: string
          telefono?: string | null
        }
        Relationships: []
      }
      profesional_tratamientos: {
        Row: {
          activo: boolean
          id: number
          profesional_id: number
          tratamiento_id: number
        }
        Insert: {
          activo?: boolean
          id?: number
          profesional_id: number
          tratamiento_id: number
        }
        Update: {
          activo?: boolean
          id?: number
          profesional_id?: number
          tratamiento_id?: number
        }
        Relationships: [
          {
            foreignKeyName: "profesional_tratamientos_profesional_id_fkey"
            columns: ["profesional_id"]
            isOneToOne: false
            referencedRelation: "profesionales"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "profesional_tratamientos_tratamiento_id_fkey"
            columns: ["tratamiento_id"]
            isOneToOne: false
            referencedRelation: "tratamientos"
            referencedColumns: ["id"]
          },
        ]
      }
      profesionales: {
        Row: {
          activo: boolean
          apellido: string
          created_at: string
          email: string
          fecha_baja: string | null
          id: number
          nombre: string
        }
        Insert: {
          activo?: boolean
          apellido: string
          created_at?: string
          email: string
          fecha_baja?: string | null
          id?: number
          nombre: string
        }
        Update: {
          activo?: boolean
          apellido?: string
          created_at?: string
          email?: string
          fecha_baja?: string | null
          id?: number
          nombre?: string
        }
        Relationships: []
      }
      tratamientos: {
        Row: {
          created_at: string
          duracion_web_min: number | null
          id: number
          nombre: string
          orden: number | null
        }
        Insert: {
          created_at?: string
          duracion_web_min?: number | null
          id?: number
          nombre: string
          orden?: number | null
        }
        Update: {
          created_at?: string
          duracion_web_min?: number | null
          id?: number
          nombre?: string
          orden?: number | null
        }
        Relationships: []
      }
      turnos: {
        Row: {
          activo: boolean
          aviso_at: string | null
          aviso_estado: string | null
          canal: string
          created_at: string
          duracion_min: number
          id: number
          inicio: string
          inicio_avisado: string | null
          motivo_consulta_id: number | null
          nota: string | null
          observaciones_paciente: string | null
          paciente_id: number
          profesional_id: number
          tratamiento_id: number | null
        }
        Insert: {
          activo?: boolean
          aviso_at?: string | null
          aviso_estado?: string | null
          canal: string
          created_at?: string
          duracion_min?: number
          id?: number
          inicio: string
          inicio_avisado?: string | null
          motivo_consulta_id?: number | null
          nota?: string | null
          observaciones_paciente?: string | null
          paciente_id: number
          profesional_id: number
          tratamiento_id?: number | null
        }
        Update: {
          activo?: boolean
          aviso_at?: string | null
          aviso_estado?: string | null
          canal?: string
          created_at?: string
          duracion_min?: number
          id?: number
          inicio?: string
          inicio_avisado?: string | null
          motivo_consulta_id?: number | null
          nota?: string | null
          observaciones_paciente?: string | null
          paciente_id?: number
          profesional_id?: number
          tratamiento_id?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "turnos_motivo_consulta_id_fkey"
            columns: ["motivo_consulta_id"]
            isOneToOne: false
            referencedRelation: "tratamientos"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "turnos_paciente_id_fkey"
            columns: ["paciente_id"]
            isOneToOne: false
            referencedRelation: "pacientes"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "turnos_profesional_id_fkey"
            columns: ["profesional_id"]
            isOneToOne: false
            referencedRelation: "profesionales"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "turnos_tratamiento_id_fkey"
            columns: ["tratamiento_id"]
            isOneToOne: false
            referencedRelation: "tratamientos"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      fin_del_turno: {
        Args: { inicio: string; minutos: number }
        Returns: string
      }
      reclamar_avisos_pendientes: {
        Args: { tope: number }
        Returns: {
          motivo_nombre: string
          paciente_apellido: string
          paciente_email: string
          paciente_nombre: string
          profesional_apellido: string
          profesional_email: string
          profesional_nombre: string
          tiene_observaciones: boolean
          tratamiento_nombre: string
          turno_activo: boolean
          turno_canal: string
          turno_duracion_min: number
          turno_id: number
          turno_inicio: string
          turno_inicio_avisado: string
        }[]
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
