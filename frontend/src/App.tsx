/**
 * Shell for the member client.
 *
 * Screens land milestone by milestone; the critical path comes first — Guild list,
 * Guild home, proposal and ballot, create proposal, consent card, rebalance status,
 * position receipt, skip explainer. Static mockups of all nineteen screens are in
 * ../../design/screens.
 *
 * Two UI rules are load-bearing rather than cosmetic (see docs/ui-spec.md):
 * dollar amounts appear only on a member's own screens, and on the consent card Skip
 * carries the same visual weight as Approve.
 */

export default function App() {
  return (
    <div className="min-h-screen bg-[#F5F3EE] text-[#12161B]">
      <main className="mx-auto flex max-w-md flex-col gap-4 px-5 py-8">
        <header className="flex flex-col gap-2">
          <p className="text-xs tracking-widest text-[#5C6570]">GUILD</p>
          <h1 className="font-serif text-3xl">A group decides. Your account acts.</h1>
        </header>

        <section className="rounded-2xl border border-[#E3DED4] bg-white p-5">
          <p className="text-sm leading-relaxed text-[#3D444C]">
            Proof of concept. Partners are simulated and no real money moves.
          </p>
        </section>
      </main>
    </div>
  );
}
