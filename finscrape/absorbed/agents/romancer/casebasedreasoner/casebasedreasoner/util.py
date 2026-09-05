import csv
import os.path
import time
import sqlite3
import sys

from casebasedreasoner import cbr, mop
import inspect
import types
import textwrap
import networkx as nx

from romancer.environment.object import LoggedDict

from casebasedreasoner.mop import MOP


def make_networkx_graph(cbrinst, exclude_mops_specced_from=None, exclude_specific_mops=None,
                        include_inheritance_edges=True, include_slot_edges=True):
    slot_edge_weight = 1.0
    spec_edge_weight = 0.1
    if exclude_mops_specced_from is None:
        exclude_mops_specced_from = []
    if exclude_specific_mops is None:
        exclude_specific_mops = []

    abstmops = [cbrinst.mops[m] for m in exclude_mops_specced_from]

    g = nx.DiGraph()
    # All nodes that end up in the graph
    mop_nodes = set()
    # Insert all nodes, then insert all edges
    for mopname in cbrinst.mops:
        thismop = cbrinst.mops[mopname]
        has_specced_from = any(abst.is_abstraction(thismop) for abst in abstmops)
        if not has_specced_from and not mopname in exclude_specific_mops:
            mop_nodes.add(mopname)
            g.add_node(thismop)

    for mopname in mop_nodes:
        thismop = cbrinst.mops[mopname]
        if include_inheritance_edges:
            for othermop in thismop.specs:
                if othermop.mop_name in mop_nodes:
                    g.add_edge(thismop, othermop.mop_name, weight=spec_edge_weight, name="spec")
        if include_slot_edges:
            for slotkey, slotval in thismop.slots.items():
                if slotval in mop_nodes or (isinstance(slotval, MOP) and slotval.mop_name in mop_nodes):
                    g.add_edge(thismop, slotval, weight=slot_edge_weight, name="slot")

    return g


def make_graphviz_graph(cbrinst, filename=None, include_inheritance_edges=True, include_slot_edges=True):
    ''' Given a CBR, returns a representation of this in graphviz format '''
    g = []

    fname = filename if filename else "cbr.dot"
    g.append(f"// dot -Kfdp -Tpng -o{fname}.png {fname}")
    g.extend(["digraph G {", "splines=true", "overlap=false"])
    moptype_to_color = {"mop": "red", "instance": "green"}

    def nodename(mopname):
        return f"n{cbrinst.mops[mopname].create_seq}"

    slot_edges = []
    core_mop_nodes = []
    default_mop_nodes = []
    non_default_mop_nodes = []

    for mopname in cbrinst.mops:
        # print("Nodes for " + str(mopname))
        this_mop = cbrinst.mops[mopname]
        curr_nodename = nodename(mopname)

        thismop_color = moptype_to_color[this_mop.mop_type]
        thislabel = [
            f"<table cellspacing=\"0\" bgcolor=\"{thismop_color}\"><tr><td colspan=\"2\" id=\"n\">{str(mopname)}</td></tr>"]
        slotnum = 0

        theseslots = this_mop.slots
        if isinstance(theseslots, LoggedDict):
            theseslots = theseslots.data
        if isinstance(theseslots, tuple):
            theseslots = { i : theseslots[i] for i in range(len(theseslots)) }

        for slotname in theseslots:
            val = theseslots[slotname]
            val_s = "lambda" if callable(val) else str(val)
            slotnum = slotnum + 1
            thislabel.append(f"<tr><td>{slotname}</td><td id=\"s{str(slotnum)}\">{val_s}</td></tr>")
            if val_s in cbrinst.mops:
                slot_edges.append(
                    f" {curr_nodename}:s{str(slotnum)} -> {nodename(val_s)}:n [color=\"black\"]")

        thislabel.append(f"</table>")
        l = "".join(thislabel)

        if this_mop.is_core_cbr_mop():
            core_mop_nodes.append(f"{curr_nodename} [shape=none label=<{l}>];")
        if this_mop.is_default_mop():
            default_mop_nodes.append(f"{curr_nodename} [shape=none label=<{l}>];")
        else:
            non_default_mop_nodes.append(f"{curr_nodename} [shape=none label=<{l}>];")

    g.append("subgraph clusterDefault {")
    g.append("label=\"Default MOPs\"")
    g.append("penwidth=3")
    g.extend(default_mop_nodes)

    g.append("  subgraph clusterCore {")
    g.append("  label=\"Core MOPs\"")
    g.append("  penwidth=3")
    g.extend(core_mop_nodes)
    g.append("  }")

    g.append("}")

    g.extend(non_default_mop_nodes)
    if include_inheritance_edges:
        for mopname in cbrinst.mops:
            # print("Edges for " + str(mopname))
            this_mop = cbrinst.mops[mopname]
            for abst in this_mop.absts:
                this_abst = abst
                if isinstance(this_abst, str):
                    this_abst = cbrinst.mops[this_abst]

                if this_abst.mop_name not in cbrinst.mops:
                    print("Weird. No node named " + abst.mop_name)
                    continue
                # print(f"    abst {abst}")
                g.append(f" {nodename(mopname)}:n -> {nodename(this_abst.mop_name)}:n [color=\"orange\"]")
            for spec in this_mop.specs:
                if spec.mop_name not in cbrinst.mops:
                    print("Weird. No node named " + spec.mop_name)
                    continue
                # print(f"    spec {spec}")
                g.append(f" {nodename(mopname)}:n -> {nodename(spec.mop_name)}:n [color=\"blue\"]")

    if include_slot_edges:
        g.append("\n".join(slot_edges))

    g.append('}')

    dot = "\n".join(g)
    if filename is not None:
        with open(filename, "w") as out_dot:
            out_dot.write(dot)
            print(f"Wrote graphviz file {filename}")

    return dot

# Given a CSV file, just insert it into sqlite as a table.
#  To avoid potential exploits, if any column names contain anything other than [a-zA-Z0-9_], refuse completely.
# Does not bother guessing type. Uses SQLite's "NUMBER" which for this would:
#   try integer, then real, and finally store as string if coercion didn't work
def insert_csv_sqlite(dbconn, csvfile, tablename):
    created_table = False
    with open(csvfile, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 0 == len(row[reader.fieldnames[0]]):
                continue
            if not created_table:
                cursor = dbconn.cursor()
                print(f"Creating table {tablename}")
                cols_types = [f"{col} NUMBER" for col in reader.fieldnames]
                create_sql = (f"CREATE TABLE IF NOT EXISTS {tablename} ({','.join(cols_types)})")
                cursor.execute(create_sql)
                created_table = True
            val_bind = ",".join(["?" for _ in reader.fieldnames])
            val_list = [row[k] for k in reader.fieldnames]
            cursor.execute(f"INSERT INTO {tablename} VALUES ({val_bind})", val_list)
    dbconn.commit()


# This code assumes it is called after export_cbr_sqlite. dbfile must exist
# Takes a map of {table_name => csv_filename} and does a naive insert.
def include_extra_csv_files_in_sqlite(dbfile, input_list):
    if not os.path.exists(dbfile):
        assert ValueError("Can only import ELCBR rules into an existing database")

    print("Appending tables rules into sqlite database")
    t_start = time.time()
    conn = sqlite3.connect(dbfile)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")

    for k, f in input_list.items():
        insert_csv_sqlite(conn, f, k)

    cursor.execute('''
        CREATE VIEW IF NOT EXISTS scenario_percepts_grouped AS
        SELECT scenariomop.mopname, scenariomop.mopid, perceptslot.slotname,
               perceptslot.val, COUNT(perceptslot.val) AS cnt,
               action_lexicon.*
           FROM mop scenariomop
            INNER JOIN slot scenarioslot on scenariomop.mopid = scenarioslot.mopid AND scenarioslot.slotname='percepts'
            INNER JOIN slot perceptgroupslot on scenarioslot.ref_mopid=perceptgroupslot.mopid
            INNER JOIN slot perceptslot on perceptgroupslot.ref_mopid=perceptslot.mopid
            LEFT JOIN action_lexicon ON perceptslot.val=action_lexicon.action_num AND perceptslot.slotname='action_taken'
         WHERE scenariomop.mopname LIKE 'I-M_ELRScenario%'
         GROUP BY scenariomop.mopid, perceptslot.slotname, perceptslot.val
    ''')
    conn.commit()
    conn.close()
    t_end = time.time()
    print(f"SQLite write complete in {t_end-t_start:.2f} seconds")


# Given a case based reasoner, export it to a sqlite database for visual inspection/experimentation
def export_cbr_sqlite(cbrinst, dbfile, extramethodnames=[], deleteifexists=True):
    t_start = time.time()
    if os.path.exists(dbfile):
        if deleteifexists:
            os.unlink(dbfile)
        else:
            print(f"Error! File {dbfile} exists and deleteifexists is False")
            return

    print(f"Beginning SQLite write to {dbfile}")
    # extramethodnames is a list of methods that should also be put in database, from the cbrinst class
    conn = sqlite3.connect(dbfile)
    cursor = conn.cursor()
    # Because slots vary wildly, using an E-A-V style antipattern

    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cbr_methods (
            methodname TEXT NOT NULL UNIQUE,
            code TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mop_type (
            mop_type TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute("INSERT INTO mop_type (mop_type) VALUES ('instance'), ('mop')")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mop (
            mopid INTEGER PRIMARY KEY,
            mopname TEXT NOT NULL,
            is_core BOOLEAN NOT NULL,
            is_default BOOLEAN NOT NULL,
            create_seq INTEGER NOT NULL DEFAULT 0,
            delete_seq INTEGER DEFAULT NULL,
            mop_type TEXT NOT NULL REFERENCES mop_type(mop_type),
            UNIQUE(mopname)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mop_abst (
            mopabstid INTEGER PRIMARY KEY,
            mopid INTEGER NOT NULL REFERENCES mop(mopid),
            abstmopid INTEGER NOT NULL REFERENCES mop(mopid),
            UNIQUE(mopid, abstmopid)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mop_spec (
            mopspecid INTEGER PRIMARY KEY,
            mopid INTEGER NOT NULL REFERENCES mop(mopid),
            specmopid INTEGER NOT NULL REFERENCES mop(mopid),
            UNIQUE(mopid, specmopid)
        )
    ''')
    # Take advantage of SQLite's type system. Can insert things of any type into the value column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS slot (
            slotid INTEGER PRIMARY KEY,
            mopid INTEGER NOT NULL REFERENCES mop(mopid),
            slotname TEXT NOT NULL,
            val NUMBER NOT NULL,
            ref_mopid INTEGER REFERENCES mop(mopid),
            is_func BOOLEAN NOT NULL
        )
    ''')

    for methodname in extramethodnames:
        method = getattr(cbrinst, methodname)
        source = inspect.getsource(method)
        cursor.execute("INSERT INTO cbr_methods (methodname, code) VALUES (?, ?)", (methodname, source))

    # Insert all MOPs first. Relationships will be set up later
    for mopname in cbrinst.mops:
        # print("Nodes for " + str(mopname))
        this_mop = cbrinst.mops[mopname]
        cursor.execute("INSERT INTO mop(mopname, is_core, is_default, mop_type, create_seq, delete_seq)"
                                  " VALUES (?, ?, ?, ?, ?, ?)",
                       (this_mop.mop_name, this_mop.is_core_cbr, this_mop.is_default, this_mop.mop_type,
                                     this_mop.create_seq, this_mop.delete_seq))
    conn.commit()

    n_mops = len(cbrinst.mops)
    progress_every = int(n_mops/5)
    progress = 0
    allmops = []
    allmops.extend(cbrinst.mops.values())
    allmops.extend(cbrinst.deleted_mops)
    for this_mop in allmops:
        if 0 == progress%progress_every:
            print(f" ... {progress}/{n_mops}")
        progress += 1
        # Yes, all the subselects are slow. If it turns out to matter, can grab the lot later
        absts = [abst if isinstance(abst, MOP) else cbrinst.mops[abst] for abst in this_mop.absts]
        abstrows = [(this_mop.mop_name, abst.mop_name) for abst in absts]
        cursor.executemany("INSERT INTO mop_abst(mopid, abstmopid) VALUES"
                           " ((SELECT mopid FROM mop WHERE mopname=?), (SELECT mopid FROM mop WHERE mopname=?))", abstrows)

        specrows = [(this_mop.mop_name, spec.mop_name) for spec in this_mop.specs]
        cursor.executemany("INSERT INTO mop_spec(mopid, specmopid) VALUES"
                           " ((SELECT mopid FROM mop WHERE mopname=?), (SELECT mopid FROM mop WHERE mopname=?))", specrows)

        theseslots = this_mop.slots
        if isinstance(theseslots, LoggedDict):
            theseslots = theseslots.data
        if isinstance(theseslots, tuple):
            theseslots = { i : theseslots[i] for i in range(len(theseslots)) }

        for slotname in theseslots:
            # Just in case the name of the slot is anything other than a string
            slotname_str = str(slotname)
            if isinstance(slotname, tuple):
                print(f"It's a tuple, bob {slotname}")
                continue
            val = theseslots[slotname]
            val_s = str(val)
            is_func = False
            if callable(val):
                try:
                    val_s = inspect.getsource(val)
                except OSError as e:
                    print(f"Source for {slotname_str} unavailable")
                    val_s = None
                is_func = True

            cursor.execute("INSERT INTO slot(mopid, slotname, val, ref_mopid, is_func) VALUES"
                           " ((SELECT mopid FROM mop WHERE mopname=?), ?, ?, (SELECT mopid FROM mop WHERE mopname=?), ?)",
                           (this_mop.mop_name, slotname_str, val_s, val_s, is_func))
    else:
        print(f" ... {progress}/{n_mops}")

    # Indices
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_slot_mop ON slot(mopid, slotname)
    ''')
    # For reading into Gephi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gephi_weights(edgetype TEXT NOT NULL, weight REAL NOT NULL, UNIQUE(edgetype))
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO gephi_weights(edgetype, weight) VALUES ('spec', 0.1), ('abst', 0.1), ('slot', 1.0)
    ''')

    # Gephi defaults to "SELECT * FROM nodes" and "SELECT * FROM edges", so these should be sensible defaults
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS nodes AS
            SELECT mopid AS id, mopname AS label, is_core, is_default, mop_type,
                   CAST(create_seq AS REAL) AS "start",
                    CASE WHEN delete_seq IS NULL THEN CAST(MAX(create_seq) OVER () AS REAL) ELSE CAST(delete_seq AS REAL) END AS "end"
                FROM mop
    ''')
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS edges AS
            WITH alledges AS (SELECT mopid AS source, specmopid AS target, 'spec' AS label, 'spec' AS hier
                                  FROM mop_spec
                              UNION ALL
                              SELECT mopid AS source, ref_mopid AS target, 'slot' AS label, 'slot' AS hier
                                  FROM slot
                                  WHERE ref_mopid IS NOT NULL)
            SELECT e.source, e.target, e.label, e.hier, COALESCE(w.weight, 1.0) AS weight,
                   MAX(n_s.start, n_t.start) AS start, MIN(n_s.end, n_t.end) AS end
               FROM alledges e
                   INNER JOIN nodes n_s ON e.source=n_s.id
                   INNER JOIN nodes n_t ON e.target=n_t.id
                   LEFT JOIN gephi_weights w ON w.edgetype=e.hier 
    ''')

    # You can adjust gephi's SQL queries. Selecting nodes_hier and edges_hier is for viewing just the inheritance hierarchy
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS nodes_hier AS
            SELECT mopid AS id, mopname AS label, is_core, is_default, mop_type
                FROM mop;
    ''')

    cursor.execute('''
        CREATE VIEW IF NOT EXISTS edges_hier AS
            SELECT mopid AS source, specmopid AS target, 'spec' AS label, 'spec' AS hier
                  FROM mop_spec;
    ''')

    cursor.execute('''
        CREATE VIEW IF NOT EXISTS nodes_nopercepts AS
            SELECT * FROM nodes WHERE label NOT LIKE 'I-M_percept%'
    ''')

    cursor.execute('''
        CREATE VIEW IF NOT EXISTS edges_nopercepts AS
             SELECT * FROM edges
                 WHERE source IN (SELECT id FROM nodes_nopercepts)
                   AND target IN (SELECT id FROM nodes_nopercepts);
   ''')

    # Rapid inspection
    # Peers are mops that derive from the same abstraction as this one does
    #   May make sense to include "... and others that specialise those ones" in future?
    cursor.execute('''
        CREATE VIEW mop_peers AS
            SELECT mop.mopid AS mopid, mop.mopname AS mopname, peer.mopid AS peermopid, peer.mopname AS peermopname
                FROM mop INNER JOIN mop_abst ma on mop.mopid=ma.mopid
                    INNER JOIN mop_spec ms ON ms.mopid=ma.abstmopid
                    INNER JOIN mop peer ON peer.mopid=ms.specmopid
    ''')

    # Chase slots references from each mop, collecting all the values recursively
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS all_slot_vals AS
        WITH RECURSIVE all_slot_vals AS (
            SELECT mop.mopid AS mopid, mop.mopname AS mopname, slot.slotname AS slotname,
                   slot.val AS slot_val, typeof(slot.val) AS slot_val_type,
                   slot.ref_mopid, slot.is_func, 0 AS depth, mop.mopname || ':' || slot.slotname AS path
                FROM mop LEFT JOIN slot ON mop.mopid = slot.mopid
                     UNION ALL
            SELECT all_slot_vals.mopid, all_slot_vals.mopname, slot.slotname,
                   slot.val, typeof(slot.val),
                   slot.ref_mopid, slot.is_func, depth+1, path || ' -> ' || refmop.mopname || ':' || slot.slotname
                FROM all_slot_vals INNER JOIN mop refmop ON all_slot_vals.ref_mopid=refmop.mopid
                INNER JOIN slot ON refmop.mopid = slot.mopid
        ), ranked_slot_vals AS (
            SELECT *, 
                RANK() OVER (PARTITION BY mopid, slotname ORDER BY depth ASC) AS slot_rank,
                MIN(slot_val) FILTER (WHERE slot_val_type IN ('integer', 'real')) OVER (PARTITION BY slotname) AS min_slot_val,
                MAX(slot_val) FILTER (WHERE slot_val_type IN ('integer', 'real')) OVER (PARTITION BY slotname) AS max_slot_val
            FROM all_slot_vals WHERE 0=is_func
        )
        SELECT *,
             CAST(max_slot_val-min_slot_val AS REAL) AS slot_val_range,
             CAST(slot_val-min_slot_val AS REAL)/CAST(max_slot_val-min_slot_val AS REAL) AS slot_val_normalised
          FROM ranked_slot_vals WHERE 1=slot_rank
    ''')

    cursor.execute('''
    CREATE VIEW IF NOT EXISTS mop_distances AS
        WITH distances AS (
          SELECT mop1.mopid AS mop1id, mop1.mopname AS mop1name, mop2.mopid AS mop2id, mop2.mopname AS mop2name,
               SUM(
                   CASE WHEN mop1.slot_val_type IN ('integer', 'real')
                           THEN -POW(mop1.slot_val_normalised-mop2.slot_val_normalised, 2)
                       WHEN mop1.slot_val_type='text'
                           THEN (mop1.slot_val=mop2.slot_val)
                    END
                  ) AS dist
          FROM all_slot_vals mop1
              INNER JOIN mop_peers on mop1.mopid=mop_peers.mopid
            INNER JOIN all_slot_vals mop2 ON mop_peers.peermopid=mop2.mopid AND mop1.slotname=mop2.slotname
            GROUP BY mop1.mopid, mop_peers.peermopid),
        matchordering AS (SELECT *,
                           ROW_NUMBER() OVER (PARTITION BY mop1id ORDER BY dist DESC, mop1name!=mop2name) AS ordering
                            FROM distances)
        SELECT * FROM matchordering
    ''')

    # Check the model for self-consistency

    # Anything other than M-ROOT here is an indicator something is wrong
    cursor.execute('''
    CREATE VIEW IF NOT EXISTS check_mop_spec_missing AS
        SELECT * FROM mop LEFT JOIN mop_spec ms on mop.mopid=ms.specmopid WHERE ms.mopid IS NULL;
    ''')

    # Specialisations and Abstractions should be completely symmetric. Anything returned by this is a problem
    cursor.execute('''
    CREATE VIEW IF NOT EXISTS check_abst_spec_assymmetry AS
        SELECT ms.mopid AS spec_mopid, ms.specmopid AS spec_specmopid, ma.mopid AS abs_mopid, ma.abstmopid AS abst_absmopid, 'abst' AS symmetry
            FROM mop_spec ms
            LEFT JOIN mop_abst ma ON ma.abstmopid=ms.mopid AND ma.mopid=ms.specmopid
            WHERE ma.mopid IS NULL
        UNION ALL
        SELECT ms.mopid AS spec_mopid, ms.specmopid AS spec_specmopid, ma.mopid AS abs_mopid, ma.abstmopid AS abst_absmopid, 'spec' AS symmetry
            FROM mop_abst ma
            LEFT JOIN mop_spec ms ON ma.abstmopid=ms.mopid AND ma.mopid=ms.specmopid
            WHERE ms.mopid IS NULL
    ''')

    cursor.execute('''
    CREATE VIEW IF NOT EXISTS elr_cbr_outcomes AS
        WITH data AS (SELECT mopname, slotname, slot_val FROM all_slot_vals
                     WHERE slotname IN ('fight_level', 'flight_level', 'freeze_level', 'dominant_response', 'outcome')
                         AND mopname LIKE 'I-M_ELRScenario%'),
                pivoted AS (SELECT mopname, -- sqlite lacks PIVOT()
                       MIN(CASE WHEN slotname='fight_level' THEN slot_val ELSE NULL END) AS fight,
                       MIN(CASE WHEN slotname='flight_level' THEN slot_val ELSE NULL END) AS flight,
                       MIN(CASE WHEN slotname='freeze_level' THEN slot_val ELSE NULL END) AS freeze,
                       MIN(CASE WHEN slotname='dominant_response' THEN slot_val ELSE NULL END) AS dominant_response,
                       MIN(CASE WHEN slotname='outcome' THEN slot_val ELSE NULL END) AS outcome
                FROM data GROUP BY mopname)
              SELECT fight, flight, freeze, dominant_response, outcome, COUNT(*) AS n_obs FROM pivoted
               GROUP BY fight, flight, freeze, dominant_response, outcome
    ''')
    conn.commit()
    conn.close()
    t_end = time.time()
    print(f"SQLite write complete in {t_end-t_start:.2f} seconds")

# For the code-based activities, we're attaching methods to classes
def __instantiatemethodonclass(instance, code):
    # Exceptionally not-robust
    try:
        method_code = compile(code, "<string>", "exec")
    except IndentationError:
        # When it came from a method on a class...
        method_code = compile(textwrap.dedent(code), "<string>", "exec")
    local_namespace = {}
    exec(method_code, globals(), local_namespace)
    method_name = list(local_namespace.keys())[0]
    method = local_namespace[method_name]
    bound_method = types.MethodType(method, instance)
    setattr(instance, method_name, bound_method)
    return method_name

# Construct a new case based reasoner given a sqlite database created by export_cbr_sqlite
def load_cbr_sqlite(dbfile, env, cbrclass):
    new_cbr = cbrclass(env, env.time)
    conn = sqlite3.connect(f'file:{dbfile}?mode=ro', uri=True)
    cursor = conn.cursor()

    cursor.execute("SELECT methodname, code FROM cbr_methods")
    for methodrow in cursor.fetchall():
        print("Inserting CBR method " + methodrow[0])
        code = methodrow[1]
        __instantiatemethodonclass(new_cbr, code)

    cursor.execute("SELECT mopid, mopname, is_core, is_default, mop_type FROM mop ORDER BY mopid ASC")
    mopqueue = cursor.fetchall()
    remaining_insert_attempts = 4 * len(mopqueue)
    while len(mopqueue) > 0:
        remaining_insert_attempts -= 1
        if 0 == remaining_insert_attempts:
            print("Bailing. Failed to insert all mops before running out of chances")
            break

        moprow = mopqueue.pop(0)
        mopid = moprow[0]
        name = moprow[1]

        if name in new_cbr.mops:
            print("Rejecting " + name + " because it has already been loaded")
            continue

        cursor.execute('''
            SELECT m.mopname FROM mop_abst q
                INNER JOIN mop m ON q.abstmopid = m.mopid
                WHERE q.mopid=?
        ''', (mopid,))

        needed_mops = []
        absts = {row[0] for row in cursor.fetchall()}
        needed_mops.extend(absts)

        is_core = (moprow[2]>0)
        is_default = (moprow[3]>0)
        mop_type = moprow[4]

        cursor.execute('''SELECT slot.slotname AS slotname, val, is_func, mop.mopname AS refmopname, TYPEOF(val) AS val_type 
                               FROM slot LEFT JOIN mop ON slot.ref_mopid=mop.mopid
                               WHERE slot.mopid=?
                           ''', (mopid,))
        slotrows = cursor.fetchall()
        slotmops = [row[3] for row in slotrows if row[3] is not None]
        needed_mops.extend(slotmops)

        # Don't love this brute force approach, but it's easy and obviously-working
        missing_mops = [needed_mopname for needed_mopname in needed_mops if needed_mopname not in new_cbr.mops]
        if len(missing_mops) > 0:
            print("Requeueing " + name + " because it needs something not yet loaded")
            mopqueue.append(moprow)
            continue

        create_slots = {}
        for slotrow in slotrows:
            slotname = slotrow[0]
            slotval = slotrow[1]
            is_func = slotrow[2]
            slot_mopname = slotrow[3]
            slot_valtype = slotrow[4]

            if is_func:
                methodname = __instantiatemethodonclass(new_cbr, slotval)
                create_slots[slotname] = getattr(new_cbr, methodname)
            elif slot_mopname is not None:
                # print("Looking up mop " + slot_mopname + " for " + slotname + " on mop " + name)
                mopref = new_cbr.mops[slot_mopname]
                create_slots[slotname] = mopref
            else:
                # SQLite's type system lets us get away with this
                if slot_valtype == 'text':
                    create_slots[slotname] = slotval
                elif slot_valtype == 'integer':
                    create_slots[slotname] = int(slotval)
                elif slot_valtype == 'real':
                    create_slots[slotname] = float(slotval)
                else:
                    sys.stderr.write(f"Error! Do not know how to interpret \"{slotval}\" as a {slot_valtype}\n")

        new_cbr.add_mop(name, absts=absts, mop_type=mop_type, slots=create_slots,
                        is_default_mop=is_default, is_core_cbr_mop=is_core)
        print("Loaded mop " + name + ", there are " + str(len(mopqueue)) + " mops left")
    return new_cbr


