-- PostgreSQL schema for the AI CRM analytics MVP.
-- This creates only the allowed CRM tables used by the backend.

CREATE TABLE IF NOT EXISTS accounts (
    id char(36) PRIMARY KEY,
    name varchar(255),
    description text,
    assigned_user_id char(36),
    team_id char(36),
    helpdesk_user_team_id char(36),
    partner_user_team_id char(36),
    helpdesk_user_role_id char(36),
    partner_user_role_id char(36),
    team_set_id char(36),
    created_by char(36),
    updated_by char(36),
    email_primary varchar(255),
    email_json text,
    phone_primary varchar(255),
    phone_json text,
    customer_type varchar(255),
    account_status varchar(255),
    industry varchar(255),
    rating varchar(255),
    gstin varchar(15),
    pan varchar(10),
    website text,
    address_type varchar(255),
    street varchar(255),
    area varchar(255),
    city varchar(255),
    state varchar(255),
    country varchar(255),
    postal_code varchar(255),
    how_old_days integer,
    untouched_since_days integer,
    geofence_radius varchar(20),
    geofence_latitude varchar(255),
    geofence_longitude varchar(255),
    contact_id_name varchar(255),
    how_old varchar(255),
    untouched_since varchar(255),
    linked_status smallint NOT NULL DEFAULT 0,
    created_via_tally smallint NOT NULL DEFAULT 0,
    created_at timestamp,
    updated_at timestamp,
    deleted_at timestamp,
    auto_updated_at timestamp,
    auto_updated_by varchar(255),
    latest_comment text,
    approval_job_status varchar(100),
    auto_number varchar(255),
    auto_number_configuration text,
    auto_number_max_count integer,
    account_test varchar(255),
    account_test_configuration text,
    account_test_max_count integer,
    automation_numbers varchar(255),
    automation_numbers_configuration text,
    automation_numbers_max_count integer,
    alliant_circuit_id integer,
    alliant_circuit_id_configuration text,
    alliant_circuit_id_max_count integer,
    recurring_wise_status smallint NOT NULL DEFAULT 0,
    recurring_module_parent_id varchar(100)
);

CREATE TABLE IF NOT EXISTS account_contact (
    id char(36) PRIMARY KEY,
    account_id char(36) NOT NULL,
    contact_id char(36) NOT NULL,
    created_by char(36),
    updated_by char(36),
    deleted_at timestamp,
    created_at timestamp,
    updated_at timestamp
);

CREATE TABLE IF NOT EXISTS account_opportunity (
    id char(36) PRIMARY KEY,
    account_id char(36) NOT NULL,
    opportunity_id char(36) NOT NULL,
    created_by char(36),
    updated_by char(36),
    deleted_at timestamp,
    created_at timestamp,
    updated_at timestamp
);

CREATE TABLE IF NOT EXISTS account_ticket (
    id char(36) PRIMARY KEY,
    account_id char(36) NOT NULL,
    ticket_id char(36) NOT NULL,
    created_by char(36),
    updated_by char(36),
    deleted_at timestamp,
    created_at timestamp,
    updated_at timestamp
);

CREATE TABLE IF NOT EXISTS activities_rel (
    id char(36) PRIMARY KEY,
    parent_module varchar(255) NOT NULL,
    parent_id char(36) NOT NULL,
    initial_module varchar(255) NOT NULL,
    initial_id char(36) NOT NULL,
    activity_module varchar(255) NOT NULL,
    activity_id varchar(255) NOT NULL,
    created_at timestamp,
    updated_at timestamp,
    deleted_at timestamp
);

CREATE TABLE IF NOT EXISTS call_campaigns (
    id char(36) PRIMARY KEY,
    name varchar(255),
    maximum_try varchar(15),
    delay_between_calls varchar(15),
    dial_type varchar(50),
    call_campaign_status varchar(30),
    date_sort varchar(30),
    module_name varchar(255),
    module_field_name varchar(255),
    module_filter varchar(255),
    select_synapse varchar(255),
    filter_json jsonb,
    query_json jsonb,
    description varchar(255),
    team_id char(36),
    team_set_id char(36),
    assigned_user_id char(36),
    work_on varchar(100),
    start_date time,
    end_time time,
    select_no_of_outbound_call varchar(255),
    live_status varchar(30),
    created_by char(36),
    updated_by char(36),
    created_at timestamp,
    updated_at timestamp,
    deleted_at timestamp,
    call_trigger_ratio integer,
    select_queue varchar(255),
    start_time time,
    assigned_to_attending_collector smallint DEFAULT 0
);

CREATE TABLE IF NOT EXISTS call_check_lists (
    id char(36) PRIMARY KEY,
    check_list_unique char(36) NOT NULL UNIQUE,
    name varchar(200),
    description text,
    is_primary smallint,
    execution_completed smallint,
    force_execution_compeleted smallint,
    phone_number varchar(255),
    number_of_try integer,
    extension varchar(100),
    module_id char(36),
    module_name varchar(100),
    assigned_user_id char(36),
    team_id char(36),
    team_set_id char(36),
    created_by char(36),
    updated_by char(36),
    created_at timestamp,
    updated_at timestamp,
    deleted_at timestamp,
    latest_comment text,
    call_campaign_id char(36),
    duration time,
    call_status varchar(255),
    call_assigned_user_id char(36),
    in_execution smallint DEFAULT 0
);

CREATE TABLE IF NOT EXISTS calls (
    id char(36) PRIMARY KEY,
    name varchar(255),
    description text,
    assigned_user_id char(36),
    team_id char(36),
    team_set_id char(36),
    created_by char(36),
    updated_by char(36),
    may_be_name varchar(100),
    direction varchar(100),
    start_date timestamp,
    end_date timestamp,
    source_number varchar(100),
    destination_number varchar(100),
    duration time,
    total_duration time,
    total_duration_minute numeric(16,2),
    call_status varchar(100),
    logged_via varchar(100),
    logged_by varchar(100),
    call_type varchar(100),
    call_back_done smallint NOT NULL DEFAULT 0,
    synapse_server varchar(255),
    synapse_recording_link varchar(255),
    synapse_unique_id varchar(255),
    blacklist_call_log smallint NOT NULL DEFAULT 0,
    created_at timestamp,
    updated_at timestamp,
    deleted_at timestamp,
    auto_updated_at timestamp,
    auto_updated_by varchar(255),
    latest_comment text,
    overall_call_rating integer NOT NULL DEFAULT 0,
    keyword_sentence_checklist jsonb,
    call_quality_metrics jsonb,
    sentiment_analysis jsonb,
    payment_promise varchar(255),
    next_step varchar(255),
    call_outcome varchar(255),
    mom text,
    summary jsonb
);

CREATE TABLE IF NOT EXISTS accounts_audit (
    id char(36) PRIMARY KEY,
    parent_id varchar(36) NOT NULL,
    field_name varchar(255) NOT NULL,
    old_value text,
    new_value text,
    updated_by char(36),
    updated_at timestamp NOT NULL
);

CREATE INDEX IF NOT EXISTS indx_accounts_deleted_at ON accounts (deleted_at);
CREATE INDEX IF NOT EXISTS indx_accounts_industry ON accounts (industry);
CREATE INDEX IF NOT EXISTS indx_accounts_customer_type ON accounts (customer_type);
CREATE INDEX IF NOT EXISTS indx_accounts_account_status ON accounts (account_status);
CREATE INDEX IF NOT EXISTS indx_accounts_assigned_user_id ON accounts (assigned_user_id);
CREATE INDEX IF NOT EXISTS indx_account_contact_account_id ON account_contact (account_id);
CREATE INDEX IF NOT EXISTS indx_account_opportunity_account_id ON account_opportunity (account_id);
CREATE INDEX IF NOT EXISTS indx_account_ticket_account_id ON account_ticket (account_id);
CREATE INDEX IF NOT EXISTS indx_activities_rel_parent_id ON activities_rel (parent_id);
CREATE INDEX IF NOT EXISTS indx_activities_rel_activity_id ON activities_rel (activity_id);
CREATE INDEX IF NOT EXISTS indx_activities_rel_parent_module ON activities_rel (parent_module);
CREATE INDEX IF NOT EXISTS indx_activities_rel_activity_module ON activities_rel (activity_module);
CREATE INDEX IF NOT EXISTS indx_call_campaigns_assigned_user_id ON call_campaigns (assigned_user_id);
CREATE INDEX IF NOT EXISTS indx_call_check_lists_campaign_id ON call_check_lists (call_campaign_id);
CREATE INDEX IF NOT EXISTS indx_calls_deleted_at ON calls (deleted_at);
CREATE INDEX IF NOT EXISTS indx_calls_call_status ON calls (call_status);
CREATE INDEX IF NOT EXISTS indx_calls_start_date ON calls (start_date);
CREATE INDEX IF NOT EXISTS indx_calls_assigned_user_id ON calls (assigned_user_id);
