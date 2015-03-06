#
# Copyright (c) 2014-2015 SUSE LLC
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#

import logging

from spacewalk.server import rhnSQL

LOG = logging.getLogger(__name__)


class SMDB(object):
    """SUSE Manager Database functions

    """
    def __init__(self):
        rhnSQL.initDB()

    def update_client_states(self, clients):
        """Query and update the database for clients to be pinged"""

        if not clients:
            return

        h = rhnSQL.prepare(rhnSQL.Statement("""
        UPDATE rhnPushClient
        SET state_id = state.id
        FROM (
            SELECT id
            FROM rhnPushClientState
            WHERE label = :state
        ) state
        WHERE name = :client_id
        """))
        h.executemany(client_id=[c['id'] for c in clients],
                      state=[c['state'] for c in clients])
        rhnSQL.commit()

    def get_checkin_clients(self, online_clients, how_many=10):
        """Return a list of client names which are scheduled for a CHECKIN

        :online_clients - a list of client names which are known to be
        online, the returned clients will be a subset of these

        :how_many - number of clients to return; the database will be
        queried for the earliest N actions that must be performed

        """
        LOG.debug("Called get_checkin_clients")
        if not online_clients:
            LOG.debug("No nodes to checkin.")
            return

        # XXX the result of now() in SQL is being cached somewhere in
        # rhnSQL (reuses the same cursor when prepare is not called with
        # force=True) or below
        query = rhnSQL.prepare("""
        SELECT DISTINCT ON (client_name)
               a.id, sa.server_id, pc.name as client_name,
               sa.status as status
        FROM  rhnServerAction sa,
              rhnAction a,
              rhnPushClient pc
        WHERE pc.server_id = sa.server_id
          AND sa.action_id = a.id
          AND sa.status IN (0, 1) -- Queued or picked up

          AND NOT EXISTS (
              -- This is like saying 'this action has no prerequisite or
              -- has a prerequisite that has completed (status = 2)
              SELECT 1
              FROM rhnServerAction sap
              WHERE sap.server_id = sa.server_id
                AND sap.action_id = a.prerequisite
                AND sap.status != 2
          )
          AND pc.name IN :online_clients
          AND earliest_action < now()
        ORDER BY client_name, earliest_action, status ASC
        LIMIT :how_many
        """)
        query.execute(online_clients=tuple(online_clients), how_many=how_many,
                      force=True)

        nodes_to_checkin = []
        while True:
            row = query.fetchone_dict()
            if not row:
                break

            # only bother the client names which are not already in progress
            if row['status'] == 0:  # 'queued'
                nodes_to_checkin.append(row['client_name'])
            else:
                LOG.debug("Skipped %s. Already in progress."
                          % row['client_name'])

        return nodes_to_checkin
