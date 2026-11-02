--
-- Job: GODMODE Database
-- Purpose: Allow approvals.status=cancelled when a run is cancelled (API cancel path).
--

-- Patch after green /api/v1 cutover (54e605f): cancel sets pending approvals to cancelled.
-- runs/tasks CHECKs already allowed cancelled; approvals CHECK did not.

BEGIN;

ALTER TABLE approvals DROP CONSTRAINT IF EXISTS approvals_status_check;
ALTER TABLE approvals ADD CONSTRAINT approvals_status_check CHECK (
    status IN ('pending', 'approved', 'rejected', 'cancelled')
);

COMMIT;
