"""Thin Streamlit presentation shell for OPRA.AI.

Presentation only: no business logic, KPI math, file parsing or dataset caching.
"""

import streamlit as st

PAGE_TITLE = "OPRA.AI"
FOUNDATION_STATUS = "Foundation scaffold only. Analytics pipeline is not implemented yet."


def main() -> None:
    """Render the foundation status page."""
    st.set_page_config(page_title=PAGE_TITLE)
    st.title("OPRA.AI")
    st.caption("Operational Performance and Recommendation Analytics")
    st.info(FOUNDATION_STATUS)


if __name__ == "__main__":
    main()
