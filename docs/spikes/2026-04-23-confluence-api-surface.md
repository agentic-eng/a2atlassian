# Confluence API surface spike — 2026-04-23

Ran against `atlassian-python-api` version **4.0.7** (via `uv pip show atlassian-python-api`).

## Full `dir(Confluence)` output

```
add_comment
add_space_permission_json_rpc
add_space_permissions
add_user
add_user_in_restricted_page
add_user_to_group
anonymous
append_page
archive_space
attach_content
attach_file
audit
avatar_set_default_for_user
avatar_upload_for_user
change_my_password
change_user_password
check_access_mode
check_long_task_result
check_long_tasks_result
check_plugin_manager_status
clean_all_caches
clean_jira_metadata_cache
clean_package_cache
close
collaborative_editing_disable
collaborative_editing_enable
collaborative_editing_get_configuration
collaborative_editing_restart
collaborative_editing_shared_draft_status
collaborative_editing_synchrony_status
content_types
convert_storage_to_view
convert_wiki_to_storage
cql
create_group
create_or_update_template
create_page
create_restricts_from_from_user
create_space
create_whiteboard
default_headers
delete
delete_attachment
delete_attachment_by_id
delete_page_property
delete_plugin
delete_space
delete_whiteboard
disable_plugin
download_attachments_from_page
enable_plugin
experimental_headers
experimental_headers_general
export_page
form_token_headers
get
get_all_blueprints_from_space
get_all_draft_pages_from_space
get_all_draft_pages_from_space_through_cql
get_all_groups
get_all_members
get_all_pages_by_label
get_all_pages_by_space_ids_confluence_cloud
get_all_pages_from_space
get_all_pages_from_space_as_generator
get_all_pages_from_space_raw
get_all_pages_from_space_trash
get_all_restictions_for_content
get_all_restrictions_for_content
get_all_restrictions_from_page_json_rpc
get_all_space_permissions
get_all_spaces
get_all_templates_from_space
get_attachment_history
get_attachments_from_content
get_blueprint_templates
get_child_id_list
get_child_pages
get_child_title_list
get_content_history
get_content_history_by_version_number
get_content_template
get_content_templates
get_descendant_page_id
get_draft_page_by_id
get_group_members
get_home_page_of_space
get_jira_metadata
get_jira_metadata_aggregated
get_license_details
get_license_max_users
get_license_remaining
get_license_user_count
get_mobile_parameters
get_page_ancestors
get_page_as_pdf
get_page_as_word
get_page_by_id
get_page_by_title
get_page_child_by_type
get_page_comments
get_page_id
get_page_labels
get_page_properties
get_page_property
get_page_space
get_pages_by_title
get_parent_content_id
get_parent_content_title
get_pdf_download_url_for_confluence_cloud
get_permissions_granted_to_anonymous_for_space
get_permissions_granted_to_group_for_space
get_permissions_granted_to_user_for_space
get_plugin_info
get_plugin_license_info
get_plugins_info
get_space
get_space_content
get_space_export
get_space_permissions
get_space_property
get_subtree_of_content_ids
get_tables_from_page
get_template_by_id
get_trashed_contents_by_space
get_user_details_by_accountid
get_user_details_by_userkey
get_user_details_by_username
get_users_from_restricts_in_page_by_type
get_whiteboard
has_unknown_attachment_error
health_check
history
is_page_content_is_already_updated
log_curl_debug
move_page
no_check_headers
page_exists
patch
post
prepend_page
put
raise_for_status
reindex
reindex_get_status
remove_content
remove_content_history
remove_content_history_in_cloud
remove_group
remove_page
remove_page_as_draft
remove_page_attachment_keep_version
remove_page_from_trash
remove_page_history
remove_page_history_keep_version
remove_page_label
remove_permissions_from_anonymous_for_space
remove_permissions_from_group_for_space
remove_permissions_from_user_for_space
remove_space_permission
remove_template
remove_trashed_contents_by_space
remove_user_from_group
remove_user_from_restricted_page
request
resource_url
response
safe_mode_headers
scrap_regex_from_page
session
set_inline_tasks_checkbox
set_page_label
set_page_property
set_permissions_to_anonymous_for_space
set_permissions_to_group_for_space
set_permissions_to_multiple_items_for_space
set_permissions_to_user_for_space
share_with_others
synchrony_disable
synchrony_enable
synchrony_get_configuration
synchrony_remove_draft
team_calendar_events
team_calendars_get_sub_calendars
team_calendars_get_sub_calendars_watching_status
update_existing_page
update_or_create
update_page
update_page_property
update_plugin_license
update_restrictions_for_page_json_rpc
upload_plugin
url_joiner
```

## Verified signatures for critical methods

```
get_page_by_id(self, page_id, expand=None, status=None, version=None)
get_page_child_by_type(self, page_id, type='page', start=None, limit=None, expand=None)
cql(self, cql, start=0, limit=None, expand=None, include_archived_spaces=None, excerpt=None)
create_page(self, space, title, body, parent_id=None, type='page', representation='storage', editor=None, full_width=False, status='current')
update_page(self, page_id, title, body=None, parent_id=None, type='page', representation='storage', minor_edit=False, version_comment=None, always_update=False, full_width=False)
get_page_by_title(self, space, title, start=0, limit=1, expand=None, type='page')
set_page_label(self, page_id, label)
set_page_property(self, page_id, data)
update_page_property(self, page_id, data)
delete_page_property(self, page_id, page_property)
get_page_property(self, page_id, page_property_key)
```

## Method names we will use in v0.4.0

| Purpose                 | atlassian-python-api method (verified)                                                                          |
|-------------------------|-----------------------------------------------------------------------------------------------------------------|
| get page by id          | `get_page_by_id(page_id, expand=None, status=None, version=None)`                                              |
| list children of page   | `get_page_child_by_type(page_id, type='page', start=None, limit=None, expand=None)`                            |
| CQL search              | `cql(cql, start=0, limit=None, expand=None, include_archived_spaces=None, excerpt=None)`                       |
| create page             | `create_page(space, title, body, parent_id=None, type='page', representation='storage', editor=None, full_width=False, status='current')` |
| update page             | `update_page(page_id, title, body=None, parent_id=None, type='page', representation='storage', minor_edit=False, version_comment=None, always_update=False, full_width=False)` |
| find page by title      | `get_page_by_title(space, title, start=0, limit=1, expand=None, type='page')`                                  |
| add labels to page      | `set_page_label(page_id, label)`                                                                                |
| set page property       | `set_page_property(page_id, data)` — native method exists (data is a dict with `key` + `value` fields)         |
| update page property    | `update_page_property(page_id, data)` — native method exists                                                   |
| delete page property    | `delete_page_property(page_id, page_property)` — native method exists                                          |
| get page property       | `get_page_property(page_id, page_property_key)` — native method exists                                         |

## Corrections and adjustments from plan assumptions

### 1. `cql` parameter order differs
The plan table showed `cql(cql, expand=None, start, limit)`. The actual signature is:
```
cql(self, cql, start=0, limit=None, expand=None, include_archived_spaces=None, excerpt=None)
```
`start` comes before `expand`, and there are two extra parameters (`include_archived_spaces`, `excerpt`). Use keyword arguments to be safe.

### 2. `create_page` has additional parameters
The plan showed `create_page(space, title, body, parent_id=..., type='page', representation='storage')`. The actual signature adds `editor=None`, `full_width=False`, and `status='current'`. The core parameters match; the extras are safe defaults.

### 3. `update_page` `body` is optional and has more params
The plan showed `update_page(page_id, title, body, ...)`. In reality `body=None` (keyword, optional). Also adds `minor_edit`, `version_comment`, `always_update`, `full_width`. The core call pattern works the same way.

### 4. `set_page_property` is a native method — no raw REST fallback needed
The plan stated "use `set_page_property` or fall back to REST raw". In v4.0.7, all four property CRUD methods exist natively:
- `set_page_property(page_id, data)` — create
- `update_page_property(page_id, data)` — update
- `get_page_property(page_id, page_property_key)` — read
- `delete_page_property(page_id, page_property)` — delete

The `data` argument is a dict. Confirm exact schema during Task 15, but no raw `put()` fallback is required.

### 5. `full_width` parameter for page width (emoji / page_width)
Both `create_page` and `update_page` accept `full_width=False`. This covers the "page_width" concern from Task 15. Emoji in page titles/bodies go through the normal `body` (storage format), so no special handling is needed beyond encoding.

### 6. Note on `get_page_by_title` vs `get_pages_by_title`
Two methods exist: `get_page_by_title` (returns single page, `limit=1` default) and `get_pages_by_title` (returns list). Use `get_page_by_title` for exact-match lookups; use `get_pages_by_title` when multiple results are expected.

## Notes for downstream tasks

- **Task 5 / 6 (client + ops):** All planned method names are present. Use keyword args for `cql()` to avoid positional order surprises.
- **Task 12 / 13 (create/update ops):** `create_page` and `update_page` signatures confirmed. Note `body=None` on `update_page` — always pass body explicitly.
- **Task 15 (page properties / emoji / width):** Native property methods cover all CRUD. `full_width` param handles page width. Raw REST via `self._confluence.put(...)` is NOT required unless undocumented Confluence Cloud fields appear.
