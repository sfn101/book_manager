--
-- PostgreSQL database dump
--

\restrict lLLhNMY7OIaXXYuEaAiFe6jJYqaIXLb84WkfKwSdoAZHEgLZFvwOgUNSAXrTL6D

-- Dumped from database version 16.10 (Ubuntu 16.10-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 17.6

-- Started on 2025-09-28 04:48:59

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 222 (class 1259 OID 33176)
-- Name: authors; Type: TABLE; Schema: public; Owner: sfn
--

CREATE TABLE public.authors (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    image_url character varying(500)
);


ALTER TABLE public.authors OWNER TO sfn;

--
-- TOC entry 3489 (class 0 OID 0)
-- Dependencies: 222
-- Name: COLUMN authors.image_url; Type: COMMENT; Schema: public; Owner: sfn
--

COMMENT ON COLUMN public.authors.image_url IS 'Open Library author photo ID for profile images';


--
-- TOC entry 221 (class 1259 OID 33175)
-- Name: authors_id_seq; Type: SEQUENCE; Schema: public; Owner: sfn
--

CREATE SEQUENCE public.authors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.authors_id_seq OWNER TO sfn;

--
-- TOC entry 3490 (class 0 OID 0)
-- Dependencies: 221
-- Name: authors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: sfn
--

ALTER SEQUENCE public.authors_id_seq OWNED BY public.authors.id;


--
-- TOC entry 228 (class 1259 OID 33218)
-- Name: book_authors; Type: TABLE; Schema: public; Owner: sfn
--

CREATE TABLE public.book_authors (
    book_id integer NOT NULL,
    author_id integer NOT NULL
);


ALTER TABLE public.book_authors OWNER TO sfn;

--
-- TOC entry 229 (class 1259 OID 33233)
-- Name: book_categories; Type: TABLE; Schema: public; Owner: sfn
--

CREATE TABLE public.book_categories (
    book_id integer NOT NULL,
    category_id integer NOT NULL
);


ALTER TABLE public.book_categories OWNER TO sfn;

--
-- TOC entry 227 (class 1259 OID 33203)
-- Name: book_languages; Type: TABLE; Schema: public; Owner: sfn
--

CREATE TABLE public.book_languages (
    book_id integer NOT NULL,
    language_id integer NOT NULL
);


ALTER TABLE public.book_languages OWNER TO sfn;

--
-- TOC entry 226 (class 1259 OID 33194)
-- Name: books; Type: TABLE; Schema: public; Owner: sfn
--

CREATE TABLE public.books (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    publication_year integer,
    cover_id character varying(50),
    open_library_id character varying(50),
    language_id integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.books OWNER TO sfn;

--
-- TOC entry 225 (class 1259 OID 33193)
-- Name: books_id_seq; Type: SEQUENCE; Schema: public; Owner: sfn
--

CREATE SEQUENCE public.books_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.books_id_seq OWNER TO sfn;

--
-- TOC entry 3491 (class 0 OID 0)
-- Dependencies: 225
-- Name: books_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: sfn
--

ALTER SEQUENCE public.books_id_seq OWNED BY public.books.id;


--
-- TOC entry 224 (class 1259 OID 33185)
-- Name: categories; Type: TABLE; Schema: public; Owner: sfn
--

CREATE TABLE public.categories (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE public.categories OWNER TO sfn;

--
-- TOC entry 223 (class 1259 OID 33184)
-- Name: categories_id_seq; Type: SEQUENCE; Schema: public; Owner: sfn
--

CREATE SEQUENCE public.categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categories_id_seq OWNER TO sfn;

--
-- TOC entry 3492 (class 0 OID 0)
-- Dependencies: 223
-- Name: categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: sfn
--

ALTER SEQUENCE public.categories_id_seq OWNED BY public.categories.id;


--
-- TOC entry 230 (class 1259 OID 33248)
-- Name: collection_books; Type: TABLE; Schema: public; Owner: sfn
--

CREATE TABLE public.collection_books (
    collection_id integer NOT NULL,
    book_id integer NOT NULL,
    added_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.collection_books OWNER TO sfn;

--
-- TOC entry 220 (class 1259 OID 33159)
-- Name: collections; Type: TABLE; Schema: public; Owner: sfn
--

CREATE TABLE public.collections (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    user_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.collections OWNER TO sfn;

--
-- TOC entry 219 (class 1259 OID 33158)
-- Name: collections_id_seq; Type: SEQUENCE; Schema: public; Owner: sfn
--

CREATE SEQUENCE public.collections_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.collections_id_seq OWNER TO sfn;

--
-- TOC entry 3493 (class 0 OID 0)
-- Dependencies: 219
-- Name: collections_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: sfn
--

ALTER SEQUENCE public.collections_id_seq OWNED BY public.collections.id;


--
-- TOC entry 216 (class 1259 OID 33140)
-- Name: languages; Type: TABLE; Schema: public; Owner: sfn
--

CREATE TABLE public.languages (
    id integer NOT NULL,
    name character varying(45) NOT NULL
);


ALTER TABLE public.languages OWNER TO sfn;

--
-- TOC entry 215 (class 1259 OID 33139)
-- Name: languages_id_seq; Type: SEQUENCE; Schema: public; Owner: sfn
--

CREATE SEQUENCE public.languages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.languages_id_seq OWNER TO sfn;

--
-- TOC entry 3494 (class 0 OID 0)
-- Dependencies: 215
-- Name: languages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: sfn
--

ALTER SEQUENCE public.languages_id_seq OWNED BY public.languages.id;


--
-- TOC entry 218 (class 1259 OID 33147)
-- Name: users; Type: TABLE; Schema: public; Owner: sfn
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(80) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    role character varying(20) DEFAULT 'user'::character varying
);


ALTER TABLE public.users OWNER TO sfn;

--
-- TOC entry 217 (class 1259 OID 33146)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: sfn
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO sfn;

--
-- TOC entry 3495 (class 0 OID 0)
-- Dependencies: 217
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: sfn
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 3294 (class 2604 OID 33179)
-- Name: authors id; Type: DEFAULT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.authors ALTER COLUMN id SET DEFAULT nextval('public.authors_id_seq'::regclass);


--
-- TOC entry 3296 (class 2604 OID 33197)
-- Name: books id; Type: DEFAULT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.books ALTER COLUMN id SET DEFAULT nextval('public.books_id_seq'::regclass);


--
-- TOC entry 3295 (class 2604 OID 33188)
-- Name: categories id; Type: DEFAULT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.categories ALTER COLUMN id SET DEFAULT nextval('public.categories_id_seq'::regclass);


--
-- TOC entry 3292 (class 2604 OID 33162)
-- Name: collections id; Type: DEFAULT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.collections ALTER COLUMN id SET DEFAULT nextval('public.collections_id_seq'::regclass);


--
-- TOC entry 3288 (class 2604 OID 33143)
-- Name: languages id; Type: DEFAULT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.languages ALTER COLUMN id SET DEFAULT nextval('public.languages_id_seq'::regclass);


--
-- TOC entry 3289 (class 2604 OID 33150)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 3312 (class 2606 OID 33183)
-- Name: authors authors_name_key; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.authors
    ADD CONSTRAINT authors_name_key UNIQUE (name);


--
-- TOC entry 3314 (class 2606 OID 33181)
-- Name: authors authors_pkey; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.authors
    ADD CONSTRAINT authors_pkey PRIMARY KEY (id);


--
-- TOC entry 3327 (class 2606 OID 33222)
-- Name: book_authors book_authors_pkey; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.book_authors
    ADD CONSTRAINT book_authors_pkey PRIMARY KEY (book_id, author_id);


--
-- TOC entry 3329 (class 2606 OID 33237)
-- Name: book_categories book_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.book_categories
    ADD CONSTRAINT book_categories_pkey PRIMARY KEY (book_id, category_id);


--
-- TOC entry 3325 (class 2606 OID 33207)
-- Name: book_languages book_languages_pkey; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.book_languages
    ADD CONSTRAINT book_languages_pkey PRIMARY KEY (book_id, language_id);


--
-- TOC entry 3321 (class 2606 OID 33202)
-- Name: books books_open_library_id_key; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.books
    ADD CONSTRAINT books_open_library_id_key UNIQUE (open_library_id);


--
-- TOC entry 3323 (class 2606 OID 33200)
-- Name: books books_pkey; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.books
    ADD CONSTRAINT books_pkey PRIMARY KEY (id);


--
-- TOC entry 3317 (class 2606 OID 33192)
-- Name: categories categories_name_key; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_name_key UNIQUE (name);


--
-- TOC entry 3319 (class 2606 OID 33190)
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- TOC entry 3331 (class 2606 OID 33253)
-- Name: collection_books collection_books_pkey; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.collection_books
    ADD CONSTRAINT collection_books_pkey PRIMARY KEY (collection_id, book_id);


--
-- TOC entry 3308 (class 2606 OID 33167)
-- Name: collections collections_pkey; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.collections
    ADD CONSTRAINT collections_pkey PRIMARY KEY (id);


--
-- TOC entry 3310 (class 2606 OID 33169)
-- Name: collections collections_user_id_name_key; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.collections
    ADD CONSTRAINT collections_user_id_name_key UNIQUE (user_id, name);


--
-- TOC entry 3300 (class 2606 OID 33145)
-- Name: languages languages_pkey; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.languages
    ADD CONSTRAINT languages_pkey PRIMARY KEY (id);


--
-- TOC entry 3302 (class 2606 OID 33157)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 3304 (class 2606 OID 33153)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 3306 (class 2606 OID 33155)
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- TOC entry 3315 (class 1259 OID 33268)
-- Name: idx_authors_image_id; Type: INDEX; Schema: public; Owner: sfn
--

CREATE INDEX idx_authors_image_id ON public.authors USING btree (image_url);


--
-- TOC entry 3335 (class 2606 OID 33228)
-- Name: book_authors fk_author; Type: FK CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.book_authors
    ADD CONSTRAINT fk_author FOREIGN KEY (author_id) REFERENCES public.authors(id) ON DELETE CASCADE;


--
-- TOC entry 3333 (class 2606 OID 33208)
-- Name: book_languages fk_book; Type: FK CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.book_languages
    ADD CONSTRAINT fk_book FOREIGN KEY (book_id) REFERENCES public.books(id) ON DELETE CASCADE;


--
-- TOC entry 3336 (class 2606 OID 33223)
-- Name: book_authors fk_book; Type: FK CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.book_authors
    ADD CONSTRAINT fk_book FOREIGN KEY (book_id) REFERENCES public.books(id) ON DELETE CASCADE;


--
-- TOC entry 3337 (class 2606 OID 33238)
-- Name: book_categories fk_book; Type: FK CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.book_categories
    ADD CONSTRAINT fk_book FOREIGN KEY (book_id) REFERENCES public.books(id) ON DELETE CASCADE;


--
-- TOC entry 3339 (class 2606 OID 33259)
-- Name: collection_books fk_book; Type: FK CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.collection_books
    ADD CONSTRAINT fk_book FOREIGN KEY (book_id) REFERENCES public.books(id) ON DELETE CASCADE;


--
-- TOC entry 3338 (class 2606 OID 33243)
-- Name: book_categories fk_category; Type: FK CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.book_categories
    ADD CONSTRAINT fk_category FOREIGN KEY (category_id) REFERENCES public.categories(id) ON DELETE CASCADE;


--
-- TOC entry 3340 (class 2606 OID 33254)
-- Name: collection_books fk_collection; Type: FK CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.collection_books
    ADD CONSTRAINT fk_collection FOREIGN KEY (collection_id) REFERENCES public.collections(id) ON DELETE CASCADE;


--
-- TOC entry 3334 (class 2606 OID 33213)
-- Name: book_languages fk_language; Type: FK CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.book_languages
    ADD CONSTRAINT fk_language FOREIGN KEY (language_id) REFERENCES public.languages(id) ON DELETE CASCADE;


--
-- TOC entry 3332 (class 2606 OID 33170)
-- Name: collections fk_user; Type: FK CONSTRAINT; Schema: public; Owner: sfn
--

ALTER TABLE ONLY public.collections
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


-- Completed on 2025-09-28 04:48:59

--
-- PostgreSQL database dump complete
--

\unrestrict lLLhNMY7OIaXXYuEaAiFe6jJYqaIXLb84WkfKwSdoAZHEgLZFvwOgUNSAXrTL6D

