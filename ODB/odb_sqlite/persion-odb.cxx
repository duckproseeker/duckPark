// This file was generated by ODB, object-relational mapping (ORM)
// compiler for C++.
//

#include <odb/pre.hxx>

#include "persion-odb.hxx"

#include <cassert>
#include <cstring>  // std::memcpy

#include <odb/schema-catalog-impl.hxx>

#include <odb/sqlite/traits.hxx>
#include <odb/sqlite/database.hxx>
#include <odb/sqlite/transaction.hxx>
#include <odb/sqlite/connection.hxx>
#include <odb/sqlite/statement.hxx>
#include <odb/sqlite/statement-cache.hxx>
#include <odb/sqlite/simple-object-statements.hxx>
#include <odb/sqlite/view-statements.hxx>
#include <odb/sqlite/container-statements.hxx>
#include <odb/sqlite/exceptions.hxx>
#include <odb/sqlite/simple-object-result.hxx>
#include <odb/sqlite/view-result.hxx>

namespace odb
{
  // Persion
  //

  struct access::object_traits_impl< ::Persion, id_sqlite >::extra_statement_cache_type
  {
    extra_statement_cache_type (
      sqlite::connection&,
      image_type&,
      id_image_type&,
      sqlite::binding&,
      sqlite::binding&)
    {
    }
  };

  access::object_traits_impl< ::Persion, id_sqlite >::id_type
  access::object_traits_impl< ::Persion, id_sqlite >::
  id (const id_image_type& i)
  {
    sqlite::database* db (0);
    ODB_POTENTIALLY_UNUSED (db);

    id_type id;
    {
      sqlite::value_traits<
          short unsigned int,
          sqlite::id_integer >::set_value (
        id,
        i.id_value,
        i.id_null);
    }

    return id;
  }

  access::object_traits_impl< ::Persion, id_sqlite >::id_type
  access::object_traits_impl< ::Persion, id_sqlite >::
  id (const image_type& i)
  {
    sqlite::database* db (0);
    ODB_POTENTIALLY_UNUSED (db);

    id_type id;
    {
      sqlite::value_traits<
          short unsigned int,
          sqlite::id_integer >::set_value (
        id,
        i._id_value,
        i._id_null);
    }

    return id;
  }

  bool access::object_traits_impl< ::Persion, id_sqlite >::
  grow (image_type& i,
        bool* t)
  {
    ODB_POTENTIALLY_UNUSED (i);
    ODB_POTENTIALLY_UNUSED (t);

    bool grew (false);

    // _id
    //
    t[0UL] = false;

    // _first
    //
    if (t[1UL])
    {
      i._first_value.capacity (i._first_size);
      grew = true;
    }

    // _last
    //
    if (t[2UL])
    {
      i._last_value.capacity (i._last_size);
      grew = true;
    }

    // _age
    //
    t[3UL] = false;

    return grew;
  }

  void access::object_traits_impl< ::Persion, id_sqlite >::
  bind (sqlite::bind* b,
        image_type& i,
        sqlite::statement_kind sk)
  {
    ODB_POTENTIALLY_UNUSED (sk);

    using namespace sqlite;

    std::size_t n (0);

    // _id
    //
    if (sk != statement_update)
    {
      b[n].type = sqlite::bind::integer;
      b[n].buffer = &i._id_value;
      b[n].is_null = &i._id_null;
      n++;
    }

    // _first
    //
    b[n].type = sqlite::image_traits<
      ::std::string,
      sqlite::id_text>::bind_value;
    b[n].buffer = i._first_value.data ();
    b[n].size = &i._first_size;
    b[n].capacity = i._first_value.capacity ();
    b[n].is_null = &i._first_null;
    n++;

    // _last
    //
    b[n].type = sqlite::image_traits<
      ::std::string,
      sqlite::id_text>::bind_value;
    b[n].buffer = i._last_value.data ();
    b[n].size = &i._last_size;
    b[n].capacity = i._last_value.capacity ();
    b[n].is_null = &i._last_null;
    n++;

    // _age
    //
    b[n].type = sqlite::bind::integer;
    b[n].buffer = &i._age_value;
    b[n].is_null = &i._age_null;
    n++;
  }

  void access::object_traits_impl< ::Persion, id_sqlite >::
  bind (sqlite::bind* b, id_image_type& i)
  {
    std::size_t n (0);
    b[n].type = sqlite::bind::integer;
    b[n].buffer = &i.id_value;
    b[n].is_null = &i.id_null;
  }

  bool access::object_traits_impl< ::Persion, id_sqlite >::
  init (image_type& i,
        const object_type& o,
        sqlite::statement_kind sk)
  {
    ODB_POTENTIALLY_UNUSED (i);
    ODB_POTENTIALLY_UNUSED (o);
    ODB_POTENTIALLY_UNUSED (sk);

    using namespace sqlite;

    bool grew (false);

    // _id
    //
    if (sk == statement_insert)
    {
      short unsigned int const& v =
        o._id;

      bool is_null (false);
      sqlite::value_traits<
          short unsigned int,
          sqlite::id_integer >::set_image (
        i._id_value,
        is_null,
        v);
      i._id_null = is_null;
    }

    // _first
    //
    {
      ::std::string const& v =
        o._first;

      bool is_null (false);
      std::size_t cap (i._first_value.capacity ());
      sqlite::value_traits<
          ::std::string,
          sqlite::id_text >::set_image (
        i._first_value,
        i._first_size,
        is_null,
        v);
      i._first_null = is_null;
      grew = grew || (cap != i._first_value.capacity ());
    }

    // _last
    //
    {
      ::std::string const& v =
        o._last;

      bool is_null (false);
      std::size_t cap (i._last_value.capacity ());
      sqlite::value_traits<
          ::std::string,
          sqlite::id_text >::set_image (
        i._last_value,
        i._last_size,
        is_null,
        v);
      i._last_null = is_null;
      grew = grew || (cap != i._last_value.capacity ());
    }

    // _age
    //
    {
      short unsigned int const& v =
        o._age;

      bool is_null (false);
      sqlite::value_traits<
          short unsigned int,
          sqlite::id_integer >::set_image (
        i._age_value,
        is_null,
        v);
      i._age_null = is_null;
    }

    return grew;
  }

  void access::object_traits_impl< ::Persion, id_sqlite >::
  init (object_type& o,
        const image_type& i,
        database* db)
  {
    ODB_POTENTIALLY_UNUSED (o);
    ODB_POTENTIALLY_UNUSED (i);
    ODB_POTENTIALLY_UNUSED (db);

    // _id
    //
    {
      short unsigned int& v =
        o._id;

      sqlite::value_traits<
          short unsigned int,
          sqlite::id_integer >::set_value (
        v,
        i._id_value,
        i._id_null);
    }

    // _first
    //
    {
      ::std::string& v =
        o._first;

      sqlite::value_traits<
          ::std::string,
          sqlite::id_text >::set_value (
        v,
        i._first_value,
        i._first_size,
        i._first_null);
    }

    // _last
    //
    {
      ::std::string& v =
        o._last;

      sqlite::value_traits<
          ::std::string,
          sqlite::id_text >::set_value (
        v,
        i._last_value,
        i._last_size,
        i._last_null);
    }

    // _age
    //
    {
      short unsigned int& v =
        o._age;

      sqlite::value_traits<
          short unsigned int,
          sqlite::id_integer >::set_value (
        v,
        i._age_value,
        i._age_null);
    }
  }

  void access::object_traits_impl< ::Persion, id_sqlite >::
  init (id_image_type& i, const id_type& id)
  {
    {
      bool is_null (false);
      sqlite::value_traits<
          short unsigned int,
          sqlite::id_integer >::set_image (
        i.id_value,
        is_null,
        id);
      i.id_null = is_null;
    }
  }

  const char access::object_traits_impl< ::Persion, id_sqlite >::persist_statement[] =
  "INSERT INTO \"Persion\" "
  "(\"id\", "
  "\"first\", "
  "\"last\", "
  "\"age\") "
  "VALUES "
  "(?, ?, ?, ?)";

  const char access::object_traits_impl< ::Persion, id_sqlite >::find_statement[] =
  "SELECT "
  "\"Persion\".\"id\", "
  "\"Persion\".\"first\", "
  "\"Persion\".\"last\", "
  "\"Persion\".\"age\" "
  "FROM \"Persion\" "
  "WHERE \"Persion\".\"id\"=?";

  const char access::object_traits_impl< ::Persion, id_sqlite >::update_statement[] =
  "UPDATE \"Persion\" "
  "SET "
  "\"first\"=?, "
  "\"last\"=?, "
  "\"age\"=? "
  "WHERE \"id\"=?";

  const char access::object_traits_impl< ::Persion, id_sqlite >::erase_statement[] =
  "DELETE FROM \"Persion\" "
  "WHERE \"id\"=?";

  const char access::object_traits_impl< ::Persion, id_sqlite >::query_statement[] =
  "SELECT "
  "\"Persion\".\"id\", "
  "\"Persion\".\"first\", "
  "\"Persion\".\"last\", "
  "\"Persion\".\"age\" "
  "FROM \"Persion\"";

  const char access::object_traits_impl< ::Persion, id_sqlite >::erase_query_statement[] =
  "DELETE FROM \"Persion\"";

  const char access::object_traits_impl< ::Persion, id_sqlite >::table_name[] =
  "\"Persion\"";

  void access::object_traits_impl< ::Persion, id_sqlite >::
  persist (database& db, object_type& obj)
  {
    ODB_POTENTIALLY_UNUSED (db);

    using namespace sqlite;

    sqlite::connection& conn (
      sqlite::transaction::current ().connection ());
    statements_type& sts (
      conn.statement_cache ().find_object<object_type> ());

    callback (db,
              static_cast<const object_type&> (obj),
              callback_event::pre_persist);

    image_type& im (sts.image ());
    binding& imb (sts.insert_image_binding ());

    if (init (im, obj, statement_insert))
      im.version++;

    im._id_null = true;

    if (im.version != sts.insert_image_version () ||
        imb.version == 0)
    {
      bind (imb.bind, im, statement_insert);
      sts.insert_image_version (im.version);
      imb.version++;
    }

    {
      id_image_type& i (sts.id_image ());
      binding& b (sts.id_image_binding ());
      if (i.version != sts.id_image_version () || b.version == 0)
      {
        bind (b.bind, i);
        sts.id_image_version (i.version);
        b.version++;
      }
    }

    insert_statement& st (sts.persist_statement ());
    if (!st.execute ())
      throw object_already_persistent ();

    obj._id = id (sts.id_image ());

    callback (db,
              static_cast<const object_type&> (obj),
              callback_event::post_persist);
  }

  void access::object_traits_impl< ::Persion, id_sqlite >::
  update (database& db, const object_type& obj)
  {
    ODB_POTENTIALLY_UNUSED (db);

    using namespace sqlite;
    using sqlite::update_statement;

    callback (db, obj, callback_event::pre_update);

    sqlite::transaction& tr (sqlite::transaction::current ());
    sqlite::connection& conn (tr.connection ());
    statements_type& sts (
      conn.statement_cache ().find_object<object_type> ());

    const id_type& id (
      obj._id);
    id_image_type& idi (sts.id_image ());
    init (idi, id);

    image_type& im (sts.image ());
    if (init (im, obj, statement_update))
      im.version++;

    bool u (false);
    binding& imb (sts.update_image_binding ());
    if (im.version != sts.update_image_version () ||
        imb.version == 0)
    {
      bind (imb.bind, im, statement_update);
      sts.update_image_version (im.version);
      imb.version++;
      u = true;
    }

    binding& idb (sts.id_image_binding ());
    if (idi.version != sts.update_id_image_version () ||
        idb.version == 0)
    {
      if (idi.version != sts.id_image_version () ||
          idb.version == 0)
      {
        bind (idb.bind, idi);
        sts.id_image_version (idi.version);
        idb.version++;
      }

      sts.update_id_image_version (idi.version);

      if (!u)
        imb.version++;
    }

    update_statement& st (sts.update_statement ());
    if (st.execute () == 0)
      throw object_not_persistent ();

    callback (db, obj, callback_event::post_update);
    pointer_cache_traits::update (db, obj);
  }

  void access::object_traits_impl< ::Persion, id_sqlite >::
  erase (database& db, const id_type& id)
  {
    using namespace sqlite;

    ODB_POTENTIALLY_UNUSED (db);

    sqlite::connection& conn (
      sqlite::transaction::current ().connection ());
    statements_type& sts (
      conn.statement_cache ().find_object<object_type> ());

    id_image_type& i (sts.id_image ());
    init (i, id);

    binding& idb (sts.id_image_binding ());
    if (i.version != sts.id_image_version () || idb.version == 0)
    {
      bind (idb.bind, i);
      sts.id_image_version (i.version);
      idb.version++;
    }

    if (sts.erase_statement ().execute () != 1)
      throw object_not_persistent ();

    pointer_cache_traits::erase (db, id);
  }

  access::object_traits_impl< ::Persion, id_sqlite >::pointer_type
  access::object_traits_impl< ::Persion, id_sqlite >::
  find (database& db, const id_type& id)
  {
    using namespace sqlite;

    {
      pointer_type p (pointer_cache_traits::find (db, id));

      if (!pointer_traits::null_ptr (p))
        return p;
    }

    sqlite::connection& conn (
      sqlite::transaction::current ().connection ());
    statements_type& sts (
      conn.statement_cache ().find_object<object_type> ());

    statements_type::auto_lock l (sts);

    if (l.locked ())
    {
      if (!find_ (sts, &id))
        return pointer_type ();
    }

    pointer_type p (
      access::object_factory<object_type, pointer_type>::create ());
    pointer_traits::guard pg (p);

    pointer_cache_traits::insert_guard ig (
      pointer_cache_traits::insert (db, id, p));

    object_type& obj (pointer_traits::get_ref (p));

    if (l.locked ())
    {
      select_statement& st (sts.find_statement ());
      ODB_POTENTIALLY_UNUSED (st);

      callback (db, obj, callback_event::pre_load);
      init (obj, sts.image (), &db);
      load_ (sts, obj, false);
      sts.load_delayed (0);
      l.unlock ();
      callback (db, obj, callback_event::post_load);
      pointer_cache_traits::load (ig.position ());
    }
    else
      sts.delay_load (id, obj, ig.position ());

    ig.release ();
    pg.release ();
    return p;
  }

  bool access::object_traits_impl< ::Persion, id_sqlite >::
  find (database& db, const id_type& id, object_type& obj)
  {
    using namespace sqlite;

    sqlite::connection& conn (
      sqlite::transaction::current ().connection ());
    statements_type& sts (
      conn.statement_cache ().find_object<object_type> ());

    statements_type::auto_lock l (sts);

    if (!find_ (sts, &id))
      return false;

    select_statement& st (sts.find_statement ());
    ODB_POTENTIALLY_UNUSED (st);

    reference_cache_traits::position_type pos (
      reference_cache_traits::insert (db, id, obj));
    reference_cache_traits::insert_guard ig (pos);

    callback (db, obj, callback_event::pre_load);
    init (obj, sts.image (), &db);
    load_ (sts, obj, false);
    sts.load_delayed (0);
    l.unlock ();
    callback (db, obj, callback_event::post_load);
    reference_cache_traits::load (pos);
    ig.release ();
    return true;
  }

  bool access::object_traits_impl< ::Persion, id_sqlite >::
  reload (database& db, object_type& obj)
  {
    using namespace sqlite;

    sqlite::connection& conn (
      sqlite::transaction::current ().connection ());
    statements_type& sts (
      conn.statement_cache ().find_object<object_type> ());

    statements_type::auto_lock l (sts);

    const id_type& id  (
      obj._id);

    if (!find_ (sts, &id))
      return false;

    select_statement& st (sts.find_statement ());
    ODB_POTENTIALLY_UNUSED (st);

    callback (db, obj, callback_event::pre_load);
    init (obj, sts.image (), &db);
    load_ (sts, obj, true);
    sts.load_delayed (0);
    l.unlock ();
    callback (db, obj, callback_event::post_load);
    return true;
  }

  bool access::object_traits_impl< ::Persion, id_sqlite >::
  find_ (statements_type& sts,
         const id_type* id)
  {
    using namespace sqlite;

    id_image_type& i (sts.id_image ());
    init (i, *id);

    binding& idb (sts.id_image_binding ());
    if (i.version != sts.id_image_version () || idb.version == 0)
    {
      bind (idb.bind, i);
      sts.id_image_version (i.version);
      idb.version++;
    }

    image_type& im (sts.image ());
    binding& imb (sts.select_image_binding ());

    if (im.version != sts.select_image_version () ||
        imb.version == 0)
    {
      bind (imb.bind, im, statement_select);
      sts.select_image_version (im.version);
      imb.version++;
    }

    select_statement& st (sts.find_statement ());

    st.execute ();
    auto_result ar (st);
    select_statement::result r (st.fetch ());

    if (r == select_statement::truncated)
    {
      if (grow (im, sts.select_image_truncated ()))
        im.version++;

      if (im.version != sts.select_image_version ())
      {
        bind (imb.bind, im, statement_select);
        sts.select_image_version (im.version);
        imb.version++;
        st.refetch ();
      }
    }

    return r != select_statement::no_data;
  }

  result< access::object_traits_impl< ::Persion, id_sqlite >::object_type >
  access::object_traits_impl< ::Persion, id_sqlite >::
  query (database&, const query_base_type& q)
  {
    using namespace sqlite;
    using odb::details::shared;
    using odb::details::shared_ptr;

    sqlite::connection& conn (
      sqlite::transaction::current ().connection ());

    statements_type& sts (
      conn.statement_cache ().find_object<object_type> ());

    image_type& im (sts.image ());
    binding& imb (sts.select_image_binding ());

    if (im.version != sts.select_image_version () ||
        imb.version == 0)
    {
      bind (imb.bind, im, statement_select);
      sts.select_image_version (im.version);
      imb.version++;
    }

    std::string text (query_statement);
    if (!q.empty ())
    {
      text += " ";
      text += q.clause ();
    }

    q.init_parameters ();
    shared_ptr<select_statement> st (
      new (shared) select_statement (
        conn,
        text,
        false,
        true,
        q.parameters_binding (),
        imb));

    st->execute ();

    shared_ptr< odb::object_result_impl<object_type> > r (
      new (shared) sqlite::object_result_impl<object_type> (
        q, st, sts, 0));

    return result<object_type> (r);
  }

  unsigned long long access::object_traits_impl< ::Persion, id_sqlite >::
  erase_query (database&, const query_base_type& q)
  {
    using namespace sqlite;

    sqlite::connection& conn (
      sqlite::transaction::current ().connection ());

    std::string text (erase_query_statement);
    if (!q.empty ())
    {
      text += ' ';
      text += q.clause ();
    }

    q.init_parameters ();
    delete_statement st (
      conn,
      text,
      q.parameters_binding ());

    return st.execute ();
  }

  // Persion_stat
  //

  bool access::view_traits_impl< ::Persion_stat, id_sqlite >::
  grow (image_type& i,
        bool* t)
  {
    ODB_POTENTIALLY_UNUSED (i);
    ODB_POTENTIALLY_UNUSED (t);

    bool grew (false);

    // count
    //
    t[0UL] = false;

    // min_age
    //
    t[1UL] = false;

    // max_age
    //
    t[2UL] = false;

    return grew;
  }

  void access::view_traits_impl< ::Persion_stat, id_sqlite >::
  bind (sqlite::bind* b,
        image_type& i)
  {
    using namespace sqlite;

    sqlite::statement_kind sk (statement_select);
    ODB_POTENTIALLY_UNUSED (sk);

    std::size_t n (0);

    // count
    //
    b[n].type = sqlite::bind::integer;
    b[n].buffer = &i.count_value;
    b[n].is_null = &i.count_null;
    n++;

    // min_age
    //
    b[n].type = sqlite::bind::integer;
    b[n].buffer = &i.min_age_value;
    b[n].is_null = &i.min_age_null;
    n++;

    // max_age
    //
    b[n].type = sqlite::bind::integer;
    b[n].buffer = &i.max_age_value;
    b[n].is_null = &i.max_age_null;
    n++;
  }

  void access::view_traits_impl< ::Persion_stat, id_sqlite >::
  init (view_type& o,
        const image_type& i,
        database* db)
  {
    ODB_POTENTIALLY_UNUSED (o);
    ODB_POTENTIALLY_UNUSED (i);
    ODB_POTENTIALLY_UNUSED (db);

    // count
    //
    {
      ::std::size_t& v =
        o.count;

      sqlite::value_traits<
          ::std::size_t,
          sqlite::id_integer >::set_value (
        v,
        i.count_value,
        i.count_null);
    }

    // min_age
    //
    {
      ::std::size_t& v =
        o.min_age;

      sqlite::value_traits<
          ::std::size_t,
          sqlite::id_integer >::set_value (
        v,
        i.min_age_value,
        i.min_age_null);
    }

    // max_age
    //
    {
      ::std::size_t& v =
        o.max_age;

      sqlite::value_traits<
          ::std::size_t,
          sqlite::id_integer >::set_value (
        v,
        i.max_age_value,
        i.max_age_null);
    }
  }

  access::view_traits_impl< ::Persion_stat, id_sqlite >::query_base_type
  access::view_traits_impl< ::Persion_stat, id_sqlite >::
  query_statement (const query_base_type& q)
  {
    query_base_type r (
      "SELECT "
      "count(\"Persion\".\"id\"), "
      "min(\"Persion\".\"age\"), "
      "max(\"Persion\".\"age\") ");

    r += "FROM \"Persion\"";

    if (!q.empty ())
    {
      r += " ";
      r += q.clause_prefix ();
      r += q;
    }

    return r;
  }

  result< access::view_traits_impl< ::Persion_stat, id_sqlite >::view_type >
  access::view_traits_impl< ::Persion_stat, id_sqlite >::
  query (database&, const query_base_type& q)
  {
    using namespace sqlite;
    using odb::details::shared;
    using odb::details::shared_ptr;

    sqlite::connection& conn (
      sqlite::transaction::current ().connection ());
    statements_type& sts (
      conn.statement_cache ().find_view<view_type> ());

    image_type& im (sts.image ());
    binding& imb (sts.image_binding ());

    if (im.version != sts.image_version () || imb.version == 0)
    {
      bind (imb.bind, im);
      sts.image_version (im.version);
      imb.version++;
    }

    const query_base_type& qs (query_statement (q));
    qs.init_parameters ();
    shared_ptr<select_statement> st (
      new (shared) select_statement (
        conn,
        qs.clause (),
        false,
        true,
        qs.parameters_binding (),
        imb));

    st->execute ();

    shared_ptr< odb::view_result_impl<view_type> > r (
      new (shared) sqlite::view_result_impl<view_type> (
        qs, st, sts, 0));

    return result<view_type> (r);
  }
}

namespace odb
{
  static bool
  create_schema (database& db, unsigned short pass, bool drop)
  {
    ODB_POTENTIALLY_UNUSED (db);
    ODB_POTENTIALLY_UNUSED (pass);
    ODB_POTENTIALLY_UNUSED (drop);

    if (drop)
    {
      switch (pass)
      {
        case 1:
        {
          return true;
        }
        case 2:
        {
          db.execute ("DROP TABLE IF EXISTS \"Persion\"");
          db.execute ("CREATE TABLE IF NOT EXISTS \"schema_version\" (\n"
                      "  \"name\" TEXT NOT NULL PRIMARY KEY,\n"
                      "  \"version\" INTEGER NOT NULL,\n"
                      "  \"migration\" INTEGER NOT NULL)");
          db.execute ("DELETE FROM \"schema_version\"\n"
                      "  WHERE \"name\" = ''");
          return false;
        }
      }
    }
    else
    {
      switch (pass)
      {
        case 1:
        {
          db.execute ("CREATE TABLE \"Persion\" (\n"
                      "  \"id\" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\n"
                      "  \"first\" TEXT NOT NULL,\n"
                      "  \"last\" TEXT NOT NULL,\n"
                      "  \"age\" INTEGER NOT NULL)");
          return true;
        }
        case 2:
        {
          db.execute ("CREATE TABLE IF NOT EXISTS \"schema_version\" (\n"
                      "  \"name\" TEXT NOT NULL PRIMARY KEY,\n"
                      "  \"version\" INTEGER NOT NULL,\n"
                      "  \"migration\" INTEGER NOT NULL)");
          db.execute ("INSERT OR IGNORE INTO \"schema_version\" (\n"
                      "  \"name\", \"version\", \"migration\")\n"
                      "  VALUES ('', 1, 0)");
          return false;
        }
      }
    }

    return false;
  }

  static const schema_catalog_create_entry
  create_schema_entry_ (
    id_sqlite,
    "",
    &create_schema);

  static const schema_catalog_migrate_entry
  migrate_schema_entry_1_ (
    id_sqlite,
    "",
    1ULL,
    0);
}

#include <odb/post.hxx>
